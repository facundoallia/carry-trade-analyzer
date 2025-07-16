#!/usr/bin/env python3
"""
Asset optimization script for production deployment
Minifies CSS and JS files for better performance
"""

import os
import re
from pathlib import Path

def minify_css(css_content):
    """Simple CSS minification"""
    # Remove comments
    css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
    # Remove extra whitespace
    css_content = re.sub(r'\s+', ' ', css_content)
    # Remove whitespace around certain characters
    css_content = re.sub(r'\s*([{}:;,>+~])\s*', r'\1', css_content)
    # Remove trailing semicolons
    css_content = re.sub(r';}', '}', css_content)
    return css_content.strip()

def minify_js(js_content):
    """Simple JS minification"""
    # Remove single-line comments (but preserve URLs)
    js_content = re.sub(r'//(?![^\n]*http)[^\n]*', '', js_content)
    # Remove multi-line comments
    js_content = re.sub(r'/\*.*?\*/', '', js_content, flags=re.DOTALL)
    # Remove extra whitespace but preserve string literals
    lines = js_content.split('\n')
    minified_lines = []
    for line in lines:
        line = line.strip()
        if line:
            minified_lines.append(line)
    return ' '.join(minified_lines)

def optimize_assets():
    """Optimize CSS and JS files for production"""
    base_path = Path(__file__).parent
    static_path = base_path / "frontend" / "static"
    
    # Minify CSS
    css_file = static_path / "css" / "style.css"
    if css_file.exists():
        with open(css_file, 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        minified_css = minify_css(css_content)
        
        # Save minified version
        minified_css_file = static_path / "css" / "style.min.css"
        with open(minified_css_file, 'w', encoding='utf-8') as f:
            f.write(minified_css)
        
        print(f"✅ CSS minified: {len(css_content)} → {len(minified_css)} bytes")
    
    # Minify JS
    js_file = static_path / "js" / "app.js"
    if js_file.exists():
        with open(js_file, 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        minified_js = minify_js(js_content)
        
        # Save minified version
        minified_js_file = static_path / "js" / "app.min.js"
        with open(minified_js_file, 'w', encoding='utf-8') as f:
            f.write(minified_js)
        
        print(f"✅ JS minified: {len(js_content)} → {len(minified_js)} bytes")

if __name__ == "__main__":
    optimize_assets()
    print("🚀 Asset optimization complete!")