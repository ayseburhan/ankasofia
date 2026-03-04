#!/usr/bin/env python3
"""
ADI ANKASOFIA - BareMetalOS Hacker IDE Sunucusu
CORS ve JSON Düzeltmeli Versiyon
"""

import os
import sys
import json
import subprocess
import threading
import webbrowser
import socket
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import shutil


class AnkasofiaRequestHandler(BaseHTTPRequestHandler):
    """Özel HTTP Request Handler"""
    
    def log_message(self, format, *args):
        """Log mesajlarını konsola yaz"""
        print(f"[{self.log_date_time_string()}] {args[0]}")

    def _set_cors_headers(self):
        """CORS başlıklarını ayarla"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')

    def _send_json_response(self, data, status=200):
        """JSON yanıtı gönder"""
        try:
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self._set_cors_headers()
            self.end_headers()
            response = json.dumps(data)
            self.wfile.write(response.encode('utf-8'))
            print(f"JSON Yanıt: {response[:100]}...")
        except Exception as e:
            print(f"JSON gönderme hatası: {e}")

    def _send_html_response(self, html_content, status=200):
        """HTML yanıtı gönder"""
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))

    def do_OPTIONS(self):
        """CORS preflight istekleri"""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        """GET isteklerini işle"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        print(f"GET isteği: {path}")

        # API endpoint'leri
        if path == '/api/files':
            self._handle_get_files()
            return
        elif path == '/api/file':
            self._handle_get_file(parsed_path)
            return
        elif path == '/api/system':
            self._handle_get_system_info()
            return
        
        # Ana sayfa ve statik dosyalar
        if path == '/' or path == '':
            path = '/ankasofia.html'
        
        # Dosyayı sun
        try:
            file_path = os.path.join(os.path.dirname(__file__), path.lstrip('/'))
            if os.path.exists(file_path) and os.path.isfile(file_path):
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                # Content-Type belirle
                content_type = 'text/plain'
                if path.endswith('.html'):
                    content_type = 'text/html; charset=utf-8'
                elif path.endswith('.css'):
                    content_type = 'text/css; charset=utf-8'
                elif path.endswith('.js'):
                    content_type = 'application/javascript; charset=utf-8'
                
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.end_headers()
                self.wfile.write(content)
            else:
                self._send_json_response({'error': f'Dosya bulunamadı: {path}'}, 404)
        except Exception as e:
            self._send_json_response({'error': str(e)}, 500)

    def do_POST(self):
        """POST isteklerini işle"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        print(f"POST isteği: {path}")

        try:
            if path == '/api/run':
                self._handle_post_run()
            elif path == '/api/save':
                self._handle_post_save()
            elif path == '/api/delete':
                self._handle_post_delete()
            elif path == '/api/new':
                self._handle_post_new()
            elif path == '/api/rename':
                self._handle_post_rename()
            elif path == '/api/execute':
                self._handle_post_execute()
            else:
                print(f"Bilinmeyen endpoint: {path}")
                self._send_json_response({'error': f'Endpoint bulunamadı: {path}'}, 404)
        except Exception as e:
            print(f"POST hatası: {e}")
            self._send_json_response({'error': str(e)}, 500)

    def _read_json_body(self):
        """Request body'den JSON oku"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                return {}
            post_data = self.rfile.read(content_length)
            return json.loads(post_data.decode('utf-8'))
        except Exception as e:
            print(f"JSON parse hatası: {e}")
            return {}

    def _handle_get_files(self):
        """Dosya listesini döndür"""
        try:
            current_dir = os.getcwd()
            files = []

            for item in os.listdir(current_dir):
                if item.startswith('.'):
                    continue

                item_path = os.path.join(current_dir, item)
                is_dir = os.path.isdir(item_path)

                files.append({
                    'name': item,
                    'type': 'directory' if is_dir else 'file',
                    'size': os.path.getsize(item_path) if not is_dir else 0,
                    'modified': os.path.getmtime(item_path)
                })

            files.sort(key=lambda x: (x['type'] == 'directory', not x['name'].endswith('.py'), x['name']))

            self._send_json_response({
                'success': True,
                'files': files,
                'current_dir': current_dir
            })

        except Exception as e:
            self._send_json_response({'success': False, 'error': str(e)}, 500)

    def _handle_get_file(self, parsed_path):
        """Dosya içeriğini oku"""
        try:
            query = parse_qs(parsed_path.query)
            filename = query.get('name', [None])[0]

            if not filename:
                self._send_json_response({'success': False, 'error': 'Dosya adı belirtilmedi'}, 400)
                return

            if '..' in filename or filename.startswith('/'):
                self._send_json_response({'success': False, 'error': 'Geçersiz dosya yolu'}, 403)
                return

            filepath = os.path.join(os.getcwd(), filename)

            if not os.path.exists(filepath):
                self._send_json_response({'success': False, 'error': 'Dosya bulunamadı'}, 404)
                return

            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            self._send_json_response({
                'success': True,
                'name': filename,
                'content': content,
                'size': len(content)
            })

        except Exception as e:
            self._send_json_response({'success': False, 'error': str(e)}, 500)

    def _handle_get_system_info(self):
        """Sistem bilgilerini döndür"""
        try:
            import platform

            info = {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
                'python_path': sys.executable,
                'current_dir': os.getcwd(),
                'cpu_count': os.cpu_count()
            }

            self._send_json_response({'success': True, 'system': info})

        except Exception as e:
            self._send_json_response({'success': False, 'error': str(e)}, 500)

    def _handle_post_run(self):
        """Python kodunu çalıştır"""
        print("Kod çalıştırma isteği alındı")
        
        data = self._read_json_body()
        code = data.get('code', '')
        
        if not code:
            self._send_json_response({'success': False, 'error': 'Kod boş'}, 400)
            return

        print(f"Kod uzunluğu: {len(code)} karakter")

        # Geçici dosya oluştur
        import tempfile
        temp_file = None
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                f.write(code)
                temp_file = f.name

            print(f"Geçici dosya: {temp_file}")

            # Kodu çalıştır
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=os.getcwd()
            )

            output = {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode,
                'success': result.returncode == 0
            }

            print(f"Çalıştırma sonucu: {result.returncode}")
            self._send_json_response({'success': True, 'output': output})

        except subprocess.TimeoutExpired:
            self._send_json_response({'success': False, 'error': 'Zaman aşımı: Kod 30 saniyeden uzun sürdü'}, 408)
        except Exception as e:
            print(f"Çalıştırma hatası: {e}")
            self._send_json_response({'success': False, 'error': f'Çalıştırma hatası: {str(e)}'}, 500)
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                    print(f"Geçici dosya silindi: {temp_file}")
                except Exception as e:
                    print(f"Geçici dosya silme hatası: {e}")

    def _handle_post_save(self):
        """Dosyayı kaydet"""
        data = self._read_json_body()
        filename = data.get('filename', '')
        content = data.get('content', '')

        if not filename:
            self._send_json_response({'success': False, 'error': 'Dosya adı belirtilmedi'}, 400)
            return

        if '..' in filename or filename.startswith('/'):
            self._send_json_response({'success': False, 'error': 'Geçersiz dosya yolu'}, 403)
            return

        try:
            filepath = os.path.join(os.getcwd(), filename)
            dir_name = os.path.dirname(filepath)
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name, exist_ok=True)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            self._send_json_response({
                'success': True,
                'message': f'Dosya kaydedildi: {filename}',
                'size': len(content)
            })

        except Exception as e:
            self._send_json_response({'success': False, 'error': str(e)}, 500)

    def _handle_post_delete(self):
        """Dosyayı sil"""
        data = self._read_json_body()
        filename = data.get('filename', '')

        if not filename:
            self._send_json_response({'success': False, 'error': 'Dosya adı belirtilmedi'}, 400)
            return

        if '..' in filename or filename.startswith('/'):
            self._send_json_response({'success': False, 'error': 'Geçersiz dosya yolu'}, 403)
            return

        try:
            filepath = os.path.join(os.getcwd(), filename)

            if not os.path.exists(filepath):
                self._send_json_response({'success': False, 'error': 'Dosya bulunamadı'}, 404)
                return

            if os.path.isdir(filepath):
                shutil.rmtree(filepath)
            else:
                os.remove(filepath)

            self._send_json_response({'success': True, 'message': f'Dosya silindi: {filename}'})

        except Exception as e:
            self._send_json_response({'success': False, 'error': str(e)}, 500)

    def _handle_post_new(self):
        """Yeni dosya/dizin oluştur"""
        data = self._read_json_body()
        name = data.get('name', '')
        is_dir = data.get('is_dir', False)

        if not name:
            self._send_json_response({'success': False, 'error': 'İsim belirtilmedi'}, 400)
            return

        if '..' in name or name.startswith('/'):
            self._send_json_response({'success': False, 'error': 'Geçersiz dosya yolu'}, 403)
            return

        try:
            filepath = os.path.join(os.getcwd(), name)

            if os.path.exists(filepath):
                self._send_json_response({'success': False, 'error': 'Dosya/dizin zaten var'}, 409)
                return

            if is_dir:
                os.makedirs(filepath, exist_ok=True)
            else:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write('# Yeni Python dosyası\n\n')

            self._send_json_response({
                'success': True,
                'message': f'{"Dizin" if is_dir else "Dosya"} oluşturuldu: {name}'
            })

        except Exception as e:
            self._send_json_response({'success': False, 'error': str(e)}, 500)

    def _handle_post_rename(self):
        """Dosya/dizini yeniden adlandır"""
        data = self._read_json_body()
        old_name = data.get('old_name', '')
        new_name = data.get('new_name', '')

        if not old_name or not new_name:
            self._send_json_response({'success': False, 'error': 'Eski veya yeni isim belirtilmedi'}, 400)
            return

        for name in [old_name, new_name]:
            if '..' in name or name.startswith('/'):
                self._send_json_response({'success': False, 'error': 'Geçersiz dosya yolu'}, 403)
                return

        try:
            old_path = os.path.join(os.getcwd(), old_name)
            new_path = os.path.join(os.getcwd(), new_name)

            if not os.path.exists(old_path):
                self._send_json_response({'success': False, 'error': 'Kaynak dosya bulunamadı'}, 404)
                return

            if os.path.exists(new_path):
                self._send_json_response({'success': False, 'error': 'Hedef dosya zaten var'}, 409)
                return

            os.rename(old_path, new_path)

            self._send_json_response({
                'success': True,
                'message': f'Dosya yeniden adlandırıldı: {old_name} -> {new_name}'
            })

        except Exception as e:
            self._send_json_response({'success': False, 'error': str(e)}, 500)

    def _handle_post_execute(self):
        """Sistem komutu çalıştır"""
        data = self._read_json_body()
        command = data.get('command', '')

        if not command:
            self._send_json_response({'success': False, 'error': 'Komut belirtilmedi'}, 400)
            return

        allowed_commands = ['dir', 'ls', 'pwd', 'cd', 'echo', 'type', 'cat', 'cls', 'clear', 'help']
        cmd_parts = command.strip().split()
        base_cmd = cmd_parts[0].lower()

        if base_cmd not in allowed_commands:
            self._send_json_response({'success': False, 'error': f'İzin verilmeyen komut: {base_cmd}'}, 403)
            return

        dangerous = ['&&', '||', ';', '`', '$', '>', '<', '|']
        if any(danger in command for danger in dangerous):
            self._send_json_response({'success': False, 'error': 'Tehlikeli karakterler içeren komut'}, 403)
            return

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=os.getcwd()
            )

            self._send_json_response({
                'success': True,
                'output': {
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'returncode': result.returncode
                }
            })

        except subprocess.TimeoutExpired:
            self._send_json_response({'success': False, 'error': 'Komut zaman aşımına uğradı'}, 408)
        except Exception as e:
            self._send_json_response({'success': False, 'error': str(e)}, 500)


def get_available_port(start_port=8000, max_attempts=50):
    """Mevcut port bul"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    return start_port


def start_server(port=8000, open_browser=True):
    """Sunucuyu başlat"""
    server_address = ('localhost', port)
    httpd = HTTPServer(server_address, AnkasofiaRequestHandler)

    print("=" * 60)
    print("ADI ANKASOFIA - BareMetalOS Hacker IDE")
    print("=" * 60)
    print(f"Sunucu: http://localhost:{port}")
    print(f"Python: {sys.executable}")
    print(f"Dizin: {os.getcwd()}")
    print("=" * 60)
    print("Çıkış: Ctrl+C")

    if open_browser:
        threading.Thread(
            target=lambda: (time.sleep(1), webbrowser.open(f'http://localhost:{port}')),
            daemon=True
        ).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nSunucu kapatılıyor...")
        httpd.shutdown()
        sys.exit(0)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='ADI ANKASOFIA Hacker IDE Sunucusu')
    parser.add_argument('--port', type=int, default=8000, help='Port numarası')
    parser.add_argument('--no-browser', action='store_true', help='Tarayıcı açma')

    args = parser.parse_args()

    port = get_available_port(args.port)
    if port != args.port:
        print(f"Port {args.port} kullanımda, {port} kullanılıyor...")

    start_server(port, not args.no_browser)