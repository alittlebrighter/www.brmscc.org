$('.datetime').each(function (index, item) {
    AnyTime.picker( $(item).attr('id'),
        {
            format: "%m/%d/%z at %h:%i%p",
            firstDOW: 0 
        });
});

$.fn.serializeObject = function() {
    var o = Object.create(null),
        elementMapper = function(element) {
            element.name = $.camelCase(element.name);
            return element;
        },
        appendToResult = function(i, element) {
            var node = o[element.name];

            if ('undefined' != typeof node && node !== null && element.value != '') {
                o[element.name] = node.push ? node.push(element.value) : [node, element.value];
            } else {
                o[element.name] = element.value;
            }
        };

    $.each($.map(this.serializeArray(), elementMapper), appendToResult);
    return o;
};

$('#click').click(function () {
    
    /*
    CKeditor doesn't put the content of its textarea into the value of
    the textarea so this function takes care of that
    */   
    $('textarea.ckeditor').each(function () {
        var $textarea = $(this);
        $textarea.val(CKEDITOR.instances[$textarea.attr('name')].getData());
    });
    
    // make ajax call to insert new resource
    $.ajax({
        url: '/api/v1/' + $('#resource').text().toLowerCase() + '/' + $('#resource').attr('resource_id'),
        cache: false,
        type: $('#resource').attr('action'),
        data : JSON.stringify($('#form').serializeObject()),
        success: function(response) {
            $('#response').text(response);
        }
    });
});
