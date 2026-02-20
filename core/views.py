from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone


def landing_page(request):
    return render(request, 'landing/index.html')


def robots_txt(request):
    sitemap_url = request.build_absolute_uri('/sitemap.xml')
    body = f"""User-agent: *
Allow: /

Sitemap: {sitemap_url}
"""
    return HttpResponse(body, content_type='text/plain; charset=utf-8')


def sitemap_xml(request):
    now_iso = timezone.now().date().isoformat()
    home_url = request.build_absolute_uri('/')
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{home_url}</loc>
    <lastmod>{now_iso}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
"""
    return HttpResponse(xml, content_type='application/xml; charset=utf-8')
