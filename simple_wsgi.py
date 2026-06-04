import urllib.parse
import json

def application(environ, start_response):
    query_string = environ.get("QUERY_STRING", "")
    get_params = urllib.parse.parse_qs(query_string)
    
    content_len = int(environ.get('CONTENT_LENGTH', 0))
    content_type = environ.get("CONTENT_TYPE", "")
    post_params = {}
    
    if content_len > 0:
        post_body = environ['wsgi.input'].read(content_len).decode('utf-8')
        
        if "application/json" in content_type:
            try:
                post_params = json.loads(post_body)
            except json.JSONDecodeError:
                post_params = {"error": "Invalid JSON"}
                
        elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            post_params = urllib.parse.parse_qs(post_body)
            
        else:
            post_params = {"raw_body": post_body}
    
    response_body = f"""
    <html>
    <body>
        <h1>WSGI Application</h1>
        <h3>GET Parameters:</h3>
        <pre>{get_params}</pre>
        
        <h3>POST Parameters:</h3>
        <pre>{post_params}</pre>
        
        <h2>Content Type:</h2>
        <p>{content_type}</p>
    </body>
    </html>
    """
    
    status = "200 OK"
    response_headers = [('Content-Type', 'text/html; charset=utf-8')]
    start_response(status, response_headers)
    
    return [response_body.encode('utf-8')]