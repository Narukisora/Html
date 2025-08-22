from vercel_wsgi import handle
from app import app

def handler(request, response):
    return handle(app, request, response)
