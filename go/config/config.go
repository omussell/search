// Package config loads environment-specific settings, mirroring settings.py.
package config

import (
	"os"
	"strings"
)

// Settings bundles every environment-driven value used across the service.
type Settings struct {
	SecretKey string

	BaseAPIURL string

	StaticCDNBaseURL string

	OrcidClientID     string
	OrcidClientSecret string
	OrcidSite         string
	OrcidAuthorizeURL string
	OrcidTokenURL     string
	OrcidMemberURL    string

	SessionLifetimeSeconds int

	APIMailto       string
	APIUserAgent    string
	ForwardClientIP bool

	AppVersion string
	Env        string
}

// Default settings that can still be overwritten via environment variables.
const (
	defaultBaseAPIURL        = "https://api.crossref.org/"
	defaultOrcidSite         = "https://api.orcid.org"
	defaultOrcidAuthorizeURL = "https://orcid.org/oauth/authorize"
	defaultOrcidTokenURL     = "https://api.orcid.org/oauth/token"
	defaultOrcidMemberURL    = "https://api.orcid.org/v3.0/"
	defaultAPIMailto         = "search@crossref.org"
	defaultUserAgentName     = "CrossrefSearch"
	defaultStaticCDNBProd    = "https://search-cdn.production.crossref.org"

	sessionLifetimeSeconds = 3600 * 24 * 30
)

// WorksAPIURL returns the base works API endpoint.
func (s *Settings) WorksAPIURL() string { return s.BaseAPIURL + "works" }

// FundersAPIURL returns the base funders API endpoint.
func (s *Settings) FundersAPIURL() string { return s.BaseAPIURL + "funders" }

// FunderWorksAPIURL returns the works-for-funder endpoint.
func (s *Settings) FunderWorksAPIURL() string { return s.BaseAPIURL + "funders/{0}/works" }

// FunderInfoAPIURL returns the single-funder info endpoint.
func (s *Settings) FunderInfoAPIURL() string { return s.BaseAPIURL + "funders/{0}" }

// JournalsAPIURL returns the works-for-journal endpoint.
func (s *Settings) JournalsAPIURL() string { return s.BaseAPIURL + "journals/{0}/works" }

func env(key, def string) string {
	if v := strings.TrimSpace(os.Getenv(key)); v != "" {
		return v
	}
	return def
}

// Load reads the environment and returns a fully populated Settings struct.
func Load() *Settings {
	envName := os.Getenv("ENV")
	// Use the CDN in production only; locally an empty base serves from disk.
	defCDN := ""
	if envName == "production" {
		defCDN = defaultStaticCDNBProd
	}

	userAgentName := env("API_USER_AGENT_NAME", defaultUserAgentName)
	version := env("APP_VERSION", "unknown")
	agent := userAgentName + "/" + version + "; mailto:" + env("API_MAILTO", defaultAPIMailto)

	return &Settings{
		SecretKey: os.Getenv("SECRET_KEY"),

		BaseAPIURL: env("BASE_API_URL", defaultBaseAPIURL),

		StaticCDNBaseURL: env("STATIC_CDN_BASE_URL", defCDN),

		OrcidClientID:     env("ORCID_CLIENT_ID", "invalid"),
		OrcidClientSecret: env("ORCID_CLIENT_SECRET", "invalid"),
		OrcidSite:         env("ORCID_SITE", defaultOrcidSite),
		OrcidAuthorizeURL: env("ORCID_AUTHORIZE_URL", defaultOrcidAuthorizeURL),
		OrcidTokenURL:     env("ORCID_TOKEN_URL", defaultOrcidTokenURL),
		OrcidMemberURL:    env("ORCID_MEMBER_URL", defaultOrcidMemberURL),

		SessionLifetimeSeconds: sessionLifetimeSeconds,

		APIMailto:       env("API_MAILTO", defaultAPIMailto),
		APIUserAgent:    agent,
		ForwardClientIP: strings.EqualFold(env("FORWARD_CLIENT_IP", "true"), "true"),

		AppVersion: version,
		Env:        envName,
	}
}
