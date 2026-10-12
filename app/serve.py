"""학습 화면을 로컬에서 띄우는 개발용 서버.

저장소 루트를 서빙한다. 실행: python app/serve.py  ->  http://localhost:8000/app/
(Windows의 기본 http.server는 .js를 text/plain으로 보내 모듈 스크립트가 막히므로 MIME을 고정한다.)
"""
import http.server
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = dict(http.server.SimpleHTTPRequestHandler.extensions_map, **{
        '.js': 'text/javascript',
        '.json': 'application/json',
        '.css': 'text/css',
        '.svg': 'image/svg+xml',
        '.sb3': 'application/zip',
    })

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    os.chdir(ROOT)
    print('http://localhost:%d/app/' % port)
    http.server.ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()
