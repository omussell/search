// Package constants mirrors the scalar and static values from core/constants.py.
package constants

import "regexp"

const (
	ConsentCookieKey   = "crossref-consent"
	ConsentCookieValue = "By using the Crossref website you have agreed to our cookie policy."

	// Categories
	CategoryHelp       = "help"
	CategoryWorks      = "works"
	CategoryFunders    = "funders"
	CategoryReferences = "references"

	// Pagination
	RowsPerPage         = 20
	MaxRows             = 1000
	PaginationPageLimit = 10
	RequestTimeOut      = 55 // seconds

	// Reference matching
	MinMatchScore = 75
	MinMatchTerms = 3
	MaxMatchTexts = 1000

	// Message categories
	MessageTypeError = "error"
	MessageTypeInfo  = "info"
	MessageTypeWarn  = "warn"

	// Search types
	SearchTypeDOI   = "doi"
	SearchTypeISSN  = "issn"
	SearchTypeORCID = "orcid"

	// Error messages
	APIRequestError = "Could not connect to Crossref REST API"
	UnknownError    = "Unknown error occurred "

	// ORCID redirects
	OrcidRedirectURL           = "auth/orcid/callback?token="
	OrcidSearchAndLinkRedirect = "auth/orcid/search-and-link"
	OrcidSessionExpired        = "You have been signed out of ORCID"

	// Session keys
	SessionOrcid = "orcid"
	AccessToken  = "access_token"
	UserName     = "user_name"
	ExpiresAt    = "expires_at"

	// Test-DOI prefixes.
	testDOI1 = "10.5555/"
	testDOI2 = "10.32013/"
	testDOI3 = "10.50505/"
)

// Work-type containers (ported from constants.py).
var (
	WorkTypesISBNAsContainer = []string{
		"book-chapter", "book-section", "book-part", "dataset",
		"component", "proceedings-article", "journal-article", "reference-entry", "report-component",
	}
	WorkTypesISSNAsContainer = []string{
		"journal-article", "journal-issue", "journal-volume", "proceedings-article", "book", "monograph",
		"reference-book", "reference-entry", "edited-book", "book-set", "book-track", "proceedings",
		"other", "book-chapter", "book-section", "book-part", "dataset", "report", "report-component",
		"component", "posted-content", "standard", "dissertation", "peer-review",
	}
)

// Compiled regexes (mirroring core/constants.py).
var (
	DOIRegex   = regexp.MustCompile(`10\.\S+/\S+$`)
	ISSNRegex  = regexp.MustCompile(`^\d{4}-\d{3}(\d|X|x)$`)
	OrcidRegex = regexp.MustCompile(`^[0-9]{4}-[0-9]{4}-[0-9]{4}-\d{3}[\dX]$`)
)

// IsTestDOI reports whether the DOI is one of the reserved test prefixes.
func IsTestDOI(doi string) bool {
	return hasPrefix(doi, testDOI1) || hasPrefix(doi, testDOI2) || hasPrefix(doi, testDOI3)
}

func hasPrefix(s, prefix string) bool {
	return len(s) >= len(prefix) && s[:len(prefix)] == prefix
}
