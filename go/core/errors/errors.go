// Package errors defines the application error types (port of core/exceptions.py).
package errors

import "fmt"

// APIConnectionException is raised when the Crossref REST API cannot be reached.
type APIConnectionException struct{ Cause error }

func (e *APIConnectionException) Error() string {
	if e.Cause == nil {
		return "api connection error"
	}
	return fmt.Sprintf("api connection error: %v", e.Cause)
}

// OrcidAPIException is a generic ORCID API error.
type OrcidAPIException struct{ Msg string }

func (e *OrcidAPIException) Error() string { return e.Msg }

// OrcidAPINotFoundException is raised by ORCID 404 responses.
type OrcidAPINotFoundException struct{ Msg string }

func (e *OrcidAPINotFoundException) Error() string { return e.Msg }

// OrcidAPIUnauthorizedException is raised by ORCID 401 responses.
type OrcidAPIUnauthorizedException struct{ Msg string }

func (e *OrcidAPIUnauthorizedException) Error() string { return e.Msg }
