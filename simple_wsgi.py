import urllib.parse

def application(environ, start_response):
    query_string = environ.get("QUERY_STRING", "")
    get_params = urllib.parse.parse_qs(query_string)
    
    content_len = int(environ.get('CONTENT_LENGTH', 0))
    post_body = environ['wsgi.input'].read(content_len).decode('utf-8')
    post_params = urllib.parse.parse_qs(post_body)
    
    response_body = f"""
    <html>
    <body>
        <h1>WSGI Application</h1>
        <h3>GET Parameters:</h3>
        <pre>{get_params}</pre>
        
        <h3>POST Parameters:</h3>
        <pre>{post_params}</pre>
    </body>
    </html>
    """
    
    status = "200 OK"
    response_headers = [('Content-Type', 'text/html; charset=utf-8')]
    start_response(status, response_headers)
    
    return [response_body.encode('utf-8')]