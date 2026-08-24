package service

import (
	"fmt"
	"html/template"
	"strconv"
	"strings"
)

// Pagination mirrors flask_paginate.Pagination with the bootstrap4 CSS
// framework, matching the HTML it emits byte-for-byte.
type Pagination struct {
	Page    int
	PerPage int
	Total   int
	Href    string
}

func NewPagination(page, total, perPage int, href string) *Pagination {
	if page < 1 {
		page = 1
	}
	return &Pagination{Page: page, PerPage: perPage, Total: total, Href: href}
}

func (p *Pagination) TotalPages() int {
	if p.PerPage < 1 {
		return 1
	}
	q, rem := p.Total/p.PerPage, p.Total%p.PerPage
	if rem > 0 {
		q++
	}
	return q
}

func (p *Pagination) pageHref(n int) string {
	if n <= 0 {
		n = 1
	}
	return strings.ReplaceAll(p.Href, "{0}", strconv.Itoa(n))
}

// pages ports flask_paginate.Pagination.pages (inner_window=2, outer_window=1).
func (p *Pagination) pages() []int {
	total := p.TotalPages()
	if total < 3 {
		out := []int{}
		for i := 1; i <= total; i++ {
			out = append(out, i)
		}
		return out
	}
	inner, outer := 2, 1
	pages := []int{}
	winFrom := p.Page - inner
	winTo := p.Page + inner
	if winTo > total {
		winFrom -= winTo - total
		winTo = total
	}
	if winFrom < 1 {
		winTo = winTo + 1 - winFrom
		winFrom = 1
		if winTo > total {
			winTo = total
		}
	}
	if winFrom > inner {
		for i := 1; i <= outer+1; i++ {
			pages = append(pages, i)
		}
		pages = append(pages, 0)
	} else {
		for i := 1; i <= winTo; i++ {
			pages = append(pages, i)
		}
	}
	if winTo < total-inner+1 {
		if winFrom > inner {
			for i := winFrom; i <= winTo; i++ {
				pages = append(pages, i)
			}
		}
		pages = append(pages, 0)
		if outer == 0 {
			pages = append(pages, total)
		} else {
			pages = append(pages, total-outer, total)
		}
	} else if winFrom > inner {
		for i := winFrom; i <= total; i++ {
			pages = append(pages, i)
		}
	} else {
		for i := winTo + 1; i <= total; i++ {
			pages = append(pages, i)
		}
	}
	return pages
}

func (p *Pagination) currentPage(n int) string {
	return fmt.Sprintf(`<li class="page-item active"><a class="page-link">%d <span class="sr-only">(current)</span></a></li>`, n)
}

func (p *Pagination) firstPage() string {
	if p.Page > 1 {
		return fmt.Sprintf(`<li class="page-item"><a class="page-link" href="%s">1</a></li>`, p.pageHref(1))
	}
	return p.currentPage(1)
}

func (p *Pagination) lastPage(total int) string {
	if p.Page < total {
		return fmt.Sprintf(`<li class="page-item"><a class="page-link" href="%s">%d</a></li>`, p.pageHref(total), total)
	}
	return p.currentPage(p.Page)
}

func (p *Pagination) singlePage(total, page int) string {
	if page == p.Page {
		return p.currentPage(page)
	}
	if page == 1 {
		return p.firstPage()
	}
	if page == total {
		return p.lastPage(total)
	}
	return fmt.Sprintf(`<li class="page-item"><a class="page-link" href="%s">%d</a></li>`, p.pageHref(page), page)
}

func (p *Pagination) prevPage() string {
	if p.Page > 1 {
		n := p.Page - 1
		if n < 1 {
			n = 1
		}
		return fmt.Sprintf(`<li class="page-item"><a class="page-link" href="%s" aria-label="Previous"><span aria-hidden="true">&laquo;</span><span class="sr-only">Previous</span></a></li>`, p.pageHref(n))
	}
	return `<li class="page-item disabled"><span class="page-link"> &laquo; </span></li>`
}

func (p *Pagination) nextPage(total int) string {
	if p.Page < total {
		return fmt.Sprintf(`<li class="page-item"><a class="page-link" href="%s" aria-label="Next"><span aria-hidden="true">&raquo;</span></a></li>`, p.pageHref(p.Page+1))
	}
	return `<li class="page-item disabled"><a class="page-link">&raquo;</a></li>`
}

// Links renders the full pagination HTML (equivalent to Pagination.links).
func (p *Pagination) Links() template.HTML {
	total := p.TotalPages()
	if total <= 1 {
		return ""
	}
	s := []string{`<nav aria-label="..."><ul class="pagination ">`}
	s = append(s, p.prevPage())
	for _, pg := range p.pages() {
		if pg == 0 {
			s = append(s, `<li class="page-item disabled"><span class="page-link">...</span></li>`)
		} else {
			s = append(s, p.singlePage(total, pg))
		}
	}
	s = append(s, p.nextPage(total))
	s = append(s, `</ul></nav>`)
	return template.HTML(strings.Join(s, ""))
}
