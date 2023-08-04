$(document).ready(function () {
    var fundersRemote = new Bloodhound({
        name: 'funders',
        datumTokenizer: function (d) {
            return d.tokens;
        },
        queryTokenizer: Bloodhound.tokenizers.whitespace,
        remote: {
            url: '/search/funders?q=%QUERY&from_ui=yes',
            filter: function (dataResponse) {
                return dataResponse;
            }
        },
        limit: 16,
        dupDetector: function (r, l) {
            return false;
        }
    });

    fundersRemote.initialize();

    var suggestionLayout = Hogan.compile('<p>{{name}} <small>{{location}}</small></p>');

    $('#search-input').typeahead(null, {
        name: 'funders',
        source: fundersRemote.ttAdapter(),
        templates: {
            suggestion: function (d) {
                return suggestionLayout.render(d)
            }
        },
        limit: 16
    });

    $('#search-input').bind('typeahead:autocompleted typeahead:selected', function (e, datum) {
        $('#fundref-input').val(datum['id']);
        $('#fundref-form').submit();
    });
});