// Package utils provides shared helpers (port of core/utils.py).
package utils

import (
	"log"
	"net/http"
	"strings"
	"time"

	"crossref_search/config"
	"crossref_search/core/session"
)

// APITimeout caps how long we wait for one API call.
const APITimeout = 60 * time.Second

// GetClientIP returns the client IP address from the request (remote addr).
func GetClientIP(r *http.Request) string {
	if r == nil {
		return ""
	}
	host, _, _ := splitHostPort(r.RemoteAddr)
	return strings.TrimSpace(host)
}

// SplitFirstXFF returns the first IP in an X-Forwarded-For header, or "".
func SplitFirstXFF(r *http.Request) string {
	if r == nil {
		return ""
	}
	xff := r.Header.Get("X-Forwarded-For")
	if xff == "" {
		return ""
	}
	return strings.TrimSpace(strings.Split(xff, ",")[0])
}

// PrepareAPIHeaders builds the base headers for any Crossref call and adds
// X-Forwarded-For when enabled and a client is available.
func PrepareAPIHeaders(cfg *config.Settings, clientIP string) map[string]string {
	h := map[string]string{"User-Agent": cfg.APIUserAgent}
	if !cfg.ForwardClientIP {
		return h
	}
	if ip := strings.TrimSpace(clientIP); ip != "" {
		h["X-Forwarded-For"] = ip
	}
	return h
}

// GetDOIReturns the public doi.org URL for a DOI.
func GetDOI(doi string) string { return "https://doi.org/" + doi }

// SignedInInfo returns (signedIn, orcidInfo, sessionExpired). When the token
// has expired, it logs and clears the session cookie.
func SignedInInfo(r *http.Request, w http.ResponseWriter, secret string) (bool, *session.Payload, bool) {
	p := session.Load(r, secret)
	if p == nil {
		return false, nil, false
	}
	if p.ExpiresAt > 0 && p.ExpiresAt <= uint64(time.Now().Unix()) {
		log.Printf("orcid session expired. expired at: %d (%s)",
			p.ExpiresAt, time.Unix(int64(p.ExpiresAt), 0).UTC().Format(time.RFC3339))
		session.Clear(w)
		return false, nil, true
	}
	return true, p, false
}

// GetHostURL returns the request's host with the scheme chosen from
// X-Forwarded-Proto (or an https default for HTTPS-only deployments).
func GetHostURL(r *http.Request) string {
	host := r.Host
	if host == "" {
		host = r.Header.Get("Host")
	}
	return "http://" + host + "/"
}

// RequestData summarises a request body / parameters for logging.
func RequestData(r *http.Request) string {
	if r == nil {
		return ""
	}
	ct := r.Header.Get("Content-Type")
	if strings.Contains(ct, "application/json") {
		return "json body"
	}
	if strings.Contains(ct, "application/x-www-form-urlencoded") {
		return "form body"
	}
	if r.URL.RawQuery != "" {
		return "query=" + r.URL.RawQuery
	}
	return "body"
}

// DOIRecordParser is a minimal helper (port of core.utils.DOIRecordParser).
func DOIRecordParser(record map[string]interface{}) (title, container, wtype, doi, url string) {
	if v, ok := record["title"].([]interface{}); ok && len(v) > 0 {
		title, _ = v[0].(string)
	}
	if v, ok := record["container-title"].([]interface{}); ok && len(v) > 0 {
		container, _ = v[0].(string)
	}
	if v, ok := record["type"].(string); ok {
		wtype = v
	}
	if v, ok := record["DOI"].(string); ok {
		doi = v
	}
	if v, ok := record["URL"].(string); ok {
		url = v
	}
	return
}

func splitHostPort(addr string) (host, port string, ok bool) {
	i := strings.LastIndex(addr, ":")
	if i < 0 {
		return addr, "", false
	}
	return addr[:i], addr[i+1:], true
}
