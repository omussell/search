// Package static_assets builds content-hashed URLs for cache busting
// (port of core/static_assets.py).
package static_assets

import (
	"crypto/sha256"
	"encoding/hex"
	"io/fs"
	"os"
	"path"
	"regexp"
	"sort"
	"strings"
	"sync"
)

const hashLength = 10

var hexRe = regexp.MustCompile(`^[0-9a-f]+$`)

type Manifest struct {
	mu        sync.RWMutex
	manifest  map[string]string // original -> hashed
	reverse   map[string]string // hashed -> original
	cdn       string
}

// NewManifest builds the original<->hashed maps by walking staticFolder.
func NewManifest(staticFolder, cdn string) *Manifest {
	m := &Manifest{manifest: map[string]string{}, reverse: map[string]string{}, cdn: cdn}
	files := []string{}
	err := fs.WalkDir(os.DirFS(staticFolder), ".", func(p string, d fs.DirEntry, err error) error {
		if err != nil || p == "." || d.IsDir() {
			return err
		}
		files = append(files, p)
		return nil
	})
	if err != nil {
		return m
	}
	sort.Strings(files)
	for _, rel := range files {
		sum, ok := m.digest(staticFolder + "/" + strings.ReplaceAll(rel, "/", string(os.PathSeparator)))
		if !ok {
			continue
		}
		hashed := hashedFilename(rel, sum)
		m.manifest[rel] = hashed
		m.reverse[hashed] = rel
	}
	return m
}

func (m *Manifest) digest(absolute string) (string, bool) {
	data, err := os.ReadFile(absolute)
	if err != nil {
		return "", false
	}
	sum := sha256.Sum256(data)
	return hex.EncodeToString(sum[:])[:hashLength], true
}

func hashedFilename(relative, digest string) string {
	base, ext := splitExt(relative)
	return base + "." + digest + ext
}

func splitExt(file string) (string, string) {
	ext := path.Ext(file)
	return file[:len(file)-len(ext)], ext
}

// URL builds the CDN/local URL for a stable filename.
func (m *Manifest) URL(filename string) string {
	m.mu.RLock()
	hashed, ok := m.manifest[filename]
	m.mu.RUnlock()
	if !ok {
		hashed = filename
	}
	return m.cdn + "/static/" + hashed
}

// ResolveFilename maps a hashed URL filename back to the on-disk file.
func (m *Manifest) ResolveFilename(requested string) (string, bool) {
	m.mu.RLock()
	orig, ok := m.reverse[requested]
	m.mu.RUnlock()
	return orig, ok
}

// StripContentHash returns "name.ext" when the path is "name.<hash>.ext".
func StripContentHash(requested string) (string, bool) {
	base, ext := splitExt(requested)
	hashSuffixLen := hashLength + 1 // "." + hash
	if len(base) <= hashSuffixLen || base[len(base)-hashSuffixLen] != '.' {
		return "", false
	}
	hash := base[len(base)-hashLength:]
	if !hexRe.MatchString(hash) {
		return "", false
	}
	return base[:len(base)-hashSuffixLen] + ext, true
}
