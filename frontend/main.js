api_url = 'http://127.0.0.1:5000'

function makeRequest() {
    url = $('#url').val()
    minute_increment = $('#minute_increment').val()

    if (!url.includes('http')) {
        $('#url-info').text('Enter a valid URL')
        $('#url').val('')
    }
    else {
        $.ajax({
            type: 'POST',
            url: api_url + '/request',
            data: JSON.stringify({"url": url, "minute_increment": minute_increment}),
            success: handleStream,
            error: handleError,
            dataType: "json",
            contentType: "application/json"
        });
    }
}

function handleStream(response) {
    request_id = response['request_id']
    text_decoder = new TextDecoder('utf-8')
    text = ''

    fetch(api_url + '/stream/' + request_id).then(response => {
        const reader = response.body.getReader();
        read_stream()
        function read_stream() {
            reader.read().then(({done, value}) => {
                if(done) {
                    return
                }
                decoded = text_decoder.decode(value)
                text = text + decoded
                $('#output-stream').text(text)
                scrollSmoothToBottom('output-stream')
                read_stream()
            })
        }
    })
}

function scrollSmoothToBottom(id) {
   var div = document.getElementById(id);
   $('#' + id).animate({
      scrollTop: div.scrollHeight - div.clientHeight
   }, 500);
}

function handleError(response) {
    $('#output-stream').text(response.statusText)
}