import threading
import os
import socket
from datetime import datetime

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 8000

# creating a TCP socket and bind it to specific port
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((SERVER_HOST, SERVER_PORT))
server_socket.listen(4)  # Max access number is 4
print('This is my HTTP Server: ', 'http://127.0.0.1:8000/test1.html')


# Get the client request
def http_client(client_socket):
    # Get the client request
    request = client_socket.recv(1024).decode()

    # Ignore request automatically sent by browser
    if 'favicon.ico' in request:
        client_socket.close()
        return

    # Send HTTP response
    response = http_server(request)
    client_socket.sendall(response)
    client_socket.close()


# Get the server request
def http_server(request):
    # default
    response = 'HTTP/1.1 400 Bad Request\n\nRequest Not Supported'
    status_code = '400 Bad Request'
    content_type = 'text/html'
    headers = request.split('\n')
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        fields = headers[0].split()
        request_type = fields[0]
        filename = fields[1]
    except IndexError:
        return response
    filepath = os.path.abspath(os.path.join('.', filename.strip('/')))

    # Get selected headers
    selected_headers_list = [headers[0]]
    for header_line in headers[1:]:
        if header_line.lower().startswith(('host:', 'connection:')):
            selected_headers_list.append(header_line)

    selected_headers = '\n'.join(selected_headers_list)
    print(f'Selected Headers:\n{selected_headers}\n')

    # Parse the request type
    if request_type == 'GET':
        # Get the content of the file
        if filename == '/':
            filename = '/test1.html'
        else:
            filename = filename[1:]  # Remove the leading '/'
        try:
            fin = open(filepath, 'rb')
            content = fin.read()
            fin.close()

            # Check if the file was modified since last request
            if 'If-Modified-Since:' in request:
                mod_time = os.path.getmtime(filepath)
                mod_time = datetime.fromtimestamp(mod_time).strftime('%a, %d %b %Y %H:%M:%S GMT')
                if_modified_since = request.split('If-Modified-Since: ')[1].split('\n')[0]
                if if_modified_since.split() == mod_time.split():
                    response = 'HTTP/1.1 304 Not Modified\n\n'
                    status_code = '304 Not Modified'
                    response = response.encode()
                    print('If-Modified-Since:', if_modified_since)
                    print(response)
                    with open('recording.log', 'a') as file:
                        file.write(f'IP Address: {SERVER_HOST} ')
                        file.write(f'Access time: {current_time} ')
                        file.write(f'Filename: {filename} ')
                        file.write(f'Status code {status_code}\n')
                return response

            # Build the response
            mod_time = os.path.getmtime(filepath)
            mod_time = datetime.fromtimestamp(mod_time).strftime('%a, %d %b %Y %H:%M:%S GMT')
            response = 'HTTP/1.1 200 OK\n'
            status_code = '200 OK'
            response += 'Last-Modified: {}\n\n'.format(mod_time)
            response = response.encode()
            if filepath.endswith('.png') or filepath.endswith('.jpg'):
                content_type = 'jpg/png'
                response += content
            else:
                response += content

        except FileNotFoundError:
            response = 'HTTP/1.1 404 Not Found\n\nFile Not Found'
            status_code = '404 Not Found'
            response = response.encode()
    else:
        response = 'HTTP/1.1 400 Bad Request\n\nRequest Not Supported'
        status_code = '400 Bad Request'
        response = response.encode()

    with open('recording.log', 'a') as file:
        file.write(f'IP Address: {SERVER_HOST} ')
        file.write(f'Access time: {current_time} ')
        file.write(f'Filename: {filename} ')
        file.write(f'Status code {status_code}\n')
    print(response)
    print('Content-Type: {}\n\n'.format(content_type))
    return response


while True:
    # Wait for client connections
    client_connection, client_address = server_socket.accept()

    # Create a new thread for each client connection
    client_thread = threading.Thread(target=http_client, args=(client_connection,))
    client_thread.start()

# Close socket
server_socket.close()
