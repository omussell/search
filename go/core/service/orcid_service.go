// Package service implements the ORCID claim logic (port of core/service/orcid_service.py).
package service

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"strconv"
	"strings"
	"time"

	"crossref_search/config"
	apperrors "crossref_search/core/errors"
	constants "crossref_search/core"
	"crossref_search/core/utils"
)

// client is a *http.Client so tests can override behaviour if needed.
var client = &http.Client{Timeout: 60 * time.Second}

// OrcidWorkType maps an internal (Crossref) work type to ORCID's vocabulary.
func OrcidWorkType(internal string) string {
	m := map[string]string{
		"journal-article":      "journal-article",
		"proceedings-article":  "conference-paper",
		"dissertation":         "dissertation-thesis",
		"report":               "report",
		"standards-and-policy": "standards-and-policy",
		"dataset":              "data-set",
		"book":                 "book",
		"journal":              "journal-issue",
		"book-chapter":         "book-chapter",
		"edited-book":          "edited-book",
		"peer-review":          "review",
		"monograph":            "book",
		"reference-book":       "book",
	}
	if v, ok := m[internal]; ok {
		return v
	}
	return "other"
}

// ExtractDate pulls date-parts[0] for pub_type, returning (year, month, day)
// where nil marks an absent component.
func ExtractDate(record map[string]interface{}, pubType string) (y, m, d *int) {
	v, ok := record[pubType]
	if !ok {
		return nil, nil, nil
	}
	pm, ok := v.(map[string]interface{})
	if !ok {
		return nil, nil, nil
	}
	dparts, ok := pm["date-parts"]
	if !ok {
		return nil, nil, nil
	}
	list, ok := dparts.([]interface{})
	if !ok || len(list) == 0 {
		return nil, nil, nil
	}
	row, ok := list[0].([]interface{})
	if !ok || len(row) == 0 {
		return nil, nil, nil
	}
	num := func(x interface{}) *int {
		f, ok := x.(float64)
		if !ok {
			return nil
		}
		i := int(f)
		return &i
	}
	switch len(row) {
	case 1:
		return num(row[0]), nil, nil
	case 2:
		return num(row[0]), num(row[1]), nil
	default:
		return num(row[0]), num(row[1]), num(row[2])
	}
}

// dateInfo is a normalised candidate date for comparison.
type dateInfo struct{ y, m, d int }

func (a dateInfo) less(b dateInfo) bool {
	if a.y != b.y {
		return a.y < b.y
	}
	if a.m != b.m {
		return a.m < b.m
	}
	return a.d < b.d
}

// AddPubDate adds the earliest of published-online/published-print to the record.
func AddPubDate(record, recordIn map[string]interface{}) {
	type cand struct {
		date   dateInfo
		hasM   bool
		hasD   bool
	}
	var earliest *cand
	for _, pub := range []string{"published-online", "published-print"} {
		y, m, day := ExtractDate(recordIn, pub)
		if y == nil {
			continue
		}
		c := cand{date: dateInfo{y: *y, m: 1, d: 1}}
		if m != nil {
			c.date.m = *m
			c.hasM = true
		}
		if day != nil {
			c.date.d = *day
			c.hasD = true
		}
		if earliest == nil || c.date.less(earliest.date) {
			earliest = &c
		}
	}
	if earliest == nil {
		return
	}
	pd := map[string]interface{}{"year": map[string]interface{}{"value": strconv.Itoa(earliest.date.y)}}
	if earliest.hasM {
		pd["month"] = map[string]interface{}{"value": fmt.Sprintf("%02d", earliest.date.m)}
	}
	if earliest.hasD {
		pd["day"] = map[string]interface{}{"value": fmt.Sprintf("%02d", earliest.date.d)}
	}
	record["publication-date"] = pd
}

func extractFirstIfArray(v interface{}) string {
	if list, ok := v.([]interface{}); ok && len(list) > 0 {
		if s, ok := list[0].(string); ok {
			return s
		}
		return ""
	}
	if s, ok := v.(string); ok {
		return s
	}
	return ""
}

// AddTitles sets title, subtitle and journal-title on the ORCID record.
func AddTitles(record, recordIn map[string]interface{}) {
	if v, ok := recordIn["title"]; ok && v != nil {
		t := map[string]interface{}{}
		if existing, ok := record["title"].(map[string]interface{}); ok {
			for k, val := range existing {
				t[k] = val
			}
		}
		t["title"] = map[string]interface{}{"value": extractFirstIfArray(v)}
		record["title"] = t
	}
	if v, ok := recordIn["subtitle"]; ok && v != nil {
		t := map[string]interface{}{}
		if existing, ok := record["title"].(map[string]interface{}); ok {
			t = existing
		}
		t["subtitle"] = map[string]interface{}{"value": extractFirstIfArray(v)}
		record["title"] = t
	}
	if v, ok := recordIn["container-title"]; ok && v != nil {
		record["journal-title"] = map[string]interface{}{"value": extractFirstIfArray(v)}
	}
}

// AddContributors adds author/editor contributors.
func AddContributors(record, recordIn map[string]interface{}) {
	contributors := []interface{}{}
	for _, role := range []string{"author", "editor"} {
		list, ok := recordIn[role].([]interface{})
		if !ok {
			continue
		}
		for _, ciRaw := range list {
			ci, ok := ciRaw.(map[string]interface{})
			if !ok {
				continue
			}
			given := asString0(ci["given"])
			family := asString0(ci["family"])
			credit := strings.TrimSpace(given + " " + family)
			if credit == "" {
				credit = strings.TrimSpace(asString0(ci["name"]))
			}
			contributor := map[string]interface{}{"credit-name": map[string]interface{}{"value": credit}}
			attrs := map[string]interface{}{"contributor-role": role}
			if seq, ok := ci["sequence"]; ok {
				attrs["contributor-sequence"] = seq
			}
			contributor["contributor-attributes"] = attrs

			orcidID := ""
			if orcidURL, ok := asString(ci["ORCID"]); ok && orcidURL != "" {
				orcidID = orcidURL
				if i := strings.LastIndex(orcidID, "/"); i >= 0 {
					orcidID = orcidID[i+1:]
				}
				contributor["contributor-orcid"] = map[string]interface{}{
					"uri":  "https://orcid.org/" + orcidID,
					"path": orcidID,
					"host": "orcid.org",
				}
			}
			if credit != "" || orcidID != "" {
				contributors = append(contributors, contributor)
			}
		}
	}
	if len(contributors) > 0 {
		record["contributors"] = map[string]interface{}{"contributor": contributors}
	}
}

func asString(v interface{}) (string, bool) {
	if s, ok := v.(string); ok {
		return s, true
	}
	return "", false
}

// AddExternalIDs adds DOI, ISBN and ISSN external identifiers.
func AddExternalIDs(record, recordIn map[string]interface{}) {
	ids := []interface{}{}
	wtype, _ := recordIn["type"].(string)

	if doi, ok := asString(recordIn["DOI"]); ok && doi != "" {
		urls, _ := asString(recordIn["URL"])
		ids = append(ids, map[string]interface{}{
			"external-id-type":         "doi",
			"external-id-value":        doi,
			"external-id-url":          map[string]interface{}{"value": urls},
			"external-id-relationship": "self",
		})
	}

	for _, key := range []string{"isbn-type", "issn-type"} {
		list, ok := recordIn[key].([]interface{})
		if !ok {
			continue
		}
		newKey := key[:len(key)-len("-type")]
		electronic, printID := "", ""
		for _, iiRaw := range list {
			ii, ok := iiRaw.(map[string]interface{})
			if !ok {
				continue
			}
			t, _ := ii["type"].(string)
			val, _ := ii["value"].(string)
			if t == "electronic" {
				electronic = val
			} else if t == "print" {
				printID = val
			}
		}
		id := electronic
		if id == "" {
			id = printID
		}
		if id == "" {
			continue
		}
		rel := "self"
		if (newKey == "isbn" && contains(constants.WorkTypesISBNAsContainer, wtype)) ||
			(newKey == "issn" && contains(constants.WorkTypesISSNAsContainer, wtype)) {
			rel = "part-of"
		}
		ids = append(ids, map[string]interface{}{
			"external-id-type":         strings.ToLower(newKey),
			"external-id-value":        id,
			"external-id-relationship": rel,
		})
	}

	if len(ids) > 0 {
		record["external-ids"] = map[string]interface{}{"external-id": ids}
	}
}

func contains(list []string, v string) bool {
	for _, x := range list {
		if x == v {
			return true
		}
	}
	return false
}

// CreateOrcidClaimJSON builds the ORCID work JSON string for a DOI record.
func CreateOrcidClaimJSON(recordIn map[string]interface{}, cfg *config.Settings, clientIP string,
	bibtex func(doi, ip string) (string, error)) (string, error) {
	out := map[string]interface{}{}
	out["type"] = OrcidWorkType(asString0(recordIn["type"]))

	if doi, ok := asString(recordIn["DOI"]); ok && doi != "" && bibtex != nil {
		if b, err := bibtex(doi, clientIP); err == nil && b != "" {
			out["citation"] = map[string]interface{}{
				"citation-type":  "bibtex",
				"citation-value": b,
			}
		}
	}

	AddExternalIDs(out, recordIn)
	AddTitles(out, recordIn)
	AddContributors(out, recordIn)
	AddPubDate(out, recordIn)

	b, err := json.Marshal(out)
	if err != nil {
		return "", err
	}
	return string(b), nil
}

func asString0(v interface{}) string {
	s, _ := asString(v)
	return s
}

// ExtractOrcidDOIs returns the lower-cased DOIs on a user's ORCID profile.
func ExtractOrcidDOIs(orcidInfo map[string]interface{}, cfg *config.Settings) ([]string, error) {
	tok := asString0(orcidInfo["access_token"])
	orcid := asString0(orcidInfo["orcid"])
	url := cfg.OrcidMemberURL + orcid + "/works"
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Accept", "application/vnd.orcid+json")
	req.Header.Set("Authorization", "Bearer "+tok)
	resp, err := client.Do(req)
	if err != nil {
		return nil, &apperrors.OrcidAPIException{Msg: err.Error()}
	}
	defer resp.Body.Close()
	switch resp.StatusCode {
	case 404:
		return nil, &apperrors.OrcidAPINotFoundException{Msg: "ORCID API returned 404 for URL: " + url}
	case 401:
		return nil, &apperrors.OrcidAPIUnauthorizedException{Msg: "Unauthorized access to ORCID API for URL: " + url}
	}
	if resp.StatusCode != 200 {
		return nil, &apperrors.OrcidAPIException{Msg: "ORCID API returned error status " + strconv.Itoa(resp.StatusCode)}
	}
	body, _ := io.ReadAll(resp.Body)
	var decoded struct {
		Group []struct {
			ExternalIDs struct {
				ExternalID []struct {
					Type  string `json:"external-id-type"`
					Value string `json:"external-id-value"`
				} `json:"external-id"`
			} `json:"external-ids"`
		} `json:"group"`
	}
	if err := json.Unmarshal(body, &decoded); err != nil {
		log.Printf("error parsing orcid json: %v", err)
		return nil, nil
	}
	out := []string{}
	for _, g := range decoded.Group {
		for _, id := range g.ExternalIDs.ExternalID {
			if strings.EqualFold(id.Type, "DOI") && id.Value != "" {
				out = append(out, strings.ToLower(id.Value))
			}
		}
	}
	return out, nil
}

// FetchCitationBibtex returns BibTeX for a DOI.
func FetchCitationBibtex(doi, clientIP string, cfg *config.Settings) (string, error) {
	u := cfg.WorksAPIURL() + "/" + doi + "/transform?mailto=" + cfg.APIMailto
	req, _ := http.NewRequest("GET", u, nil)
	for k, v := range utils.PrepareAPIHeaders(cfg, clientIP) {
		req.Header.Set(k, v)
	}
	req.Header.Set("Accept", "application/x-bibtex")
	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return "", fmt.Errorf("status %d", resp.StatusCode)
	}
	b, _ := io.ReadAll(resp.Body)
	return string(b), nil
}
