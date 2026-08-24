// Package session provides a signed-cookie session and helper middleware
// (flash messages, CSRF token) mirroring the Flask session behaviour.
package session

import (
	"crypto/hmac"
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"net/http"
	"strings"
	"time"
)

const (
	SessionCookie   = "crossref_session"
	CsrfCookie      = "csrf_token"
	FlashCookie     = "flashed"
	cookieLifetime  = time.Hour * 24 * 30
)

// FlashMessage is a single flash notification (category + message).
type FlashMessage struct {
	Category string
	Message  string
}

// Payload is the session data kept in the signed cookie.
type Payload struct {
	OrCID       string
	UserName    string
	AccessToken string
	ExpiresAt   uint64 // unix seconds
}

func b64encode(b []byte) string { return base64.RawURLEncoding.EncodeToString(b) }

func b64decode(s string) ([]byte, error) { return base64.RawURLEncoding.DecodeString(s) }

// Sign produces a signed payload for cookie storage (data.sig).
func Sign(key string, data []byte) string {
	mac := hmac.New(sha256.New, []byte(key))
	mac.Write(data)
	return b64encode(data) + "." + b64encode(mac.Sum(nil))
}

// Unsign returns the stored data when the signature is valid.
func Unsign(key, value string) ([]byte, bool) {
	parts := strings.SplitN(value, ".", 2)
	if len(parts) != 2 {
		return nil, false
	}
	data, err1 := b64decode(parts[0])
	sig, err2 := b64decode(parts[1])
	if err1 != nil || err2 != nil {
		return nil, false
	}
	mac := hmac.New(sha256.New, []byte(key))
	mac.Write(data)
	return data, hmac.Equal(sig, mac.Sum(nil))
}

// Load returns the current session payload for the request.
func Load(r *http.Request, secret string) *Payload {
	c, err := r.Cookie(SessionCookie)
	if err != nil {
		return nil
	}
	data, ok := Unsign(secret, c.Value)
	if !ok {
		return nil
	}
	var p Payload
	if err := json.Unmarshal(data, &p); err != nil {
		return nil
	}
	return &p
}

// Save serialises the payload into the session cookie.
func Save(w http.ResponseWriter, secret string, p *Payload) {
	data, _ := json.Marshal(p)
	signed := Sign(secret, data)
	http.SetCookie(w, &http.Cookie{
		Name:     SessionCookie,
		Value:    signed,
		Path:     "/",
		Secure:   true,
		HttpOnly: true,
		SameSite: http.SameSiteLaxMode,
		Expires:  time.Now().Add(cookieLifetime).UTC(),
	})
}

// Clear drops the session cookie.
func Clear(w http.ResponseWriter) {
	http.SetCookie(w, &http.Cookie{
		Name: SessionCookie, Value: "", Path: "/", MaxAge: -1, SameSite: http.SameSiteLaxMode,
	})
}

// Flash stores flash messages in a cookie and later retrieves+clears them.
type Flash struct{ key, secret string }

func NewFlash(key, secret string) *Flash { return &Flash{key: key, secret: secret} }

func (f *Flash) Push(w http.ResponseWriter, msgs []FlashMessage) {
	data, _ := json.Marshal(msgs)
	http.SetCookie(w, &http.Cookie{
		Name: f.key, Value: Sign(f.secret, data), Path: "/",
		Secure: true, HttpOnly: true, SameSite: http.SameSiteLaxMode,
		Expires: time.Now().Add(time.Hour * 2).UTC(),
	})
}

// Pop returns and clears the pending flash messages.
func (f *Flash) Pop(r *http.Request, w http.ResponseWriter) []FlashMessage {
	c, err := r.Cookie(f.key)
	if err != nil {
		return nil
	}
	data, ok := Unsign(f.secret, c.Value)
	if !ok {
		return nil
	}
	var msgs []FlashMessage
	if err := json.Unmarshal(data, &msgs); err != nil {
		return nil
	}
	http.SetCookie(w, &http.Cookie{Name: f.key, Value: "", Path: "/", MaxAge: -1, SameSite: http.SameSiteLaxMode})
	return msgs
}

// NewCSRFToken returns a random token and sets the CSRF cookie.
func NewCSRFToken(w http.ResponseWriter) string {
	buf := make([]byte, 32)
	if _, err := rand.Read(buf); err != nil {
		return ""
	}
	tok := b64encode(buf)
	http.SetCookie(w, &http.Cookie{
		Name: CsrfCookie, Value: tok, Path: "/",
		Secure: true, HttpOnly: true, SameSite: http.SameSiteLaxMode,
	})
	return tok
}
