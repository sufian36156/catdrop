import math
import struct
import zlib
import os

def write_png(filename, width, height, pixels):
    raw = bytearray()
    for y in range(height):
        raw.append(0) # filter type 0
        start = y * width * 4
        raw.extend(pixels[start:start + width * 4])
    compressed = zlib.compress(bytes(raw), level=9)
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + chunk(b'IDAT', compressed) + chunk(b'IEND', b'')
    with open(filename, 'wb') as f:
        f.write(png)

def generate_icon(size, out_path, full_square=False):
    buf = bytearray(size * size * 4)
    scale = size / 512.0
    
    def blend(x, y, r, g, b, a):
        if not (0 <= x < size and 0 <= y < size) or a <= 0:
            return
        idx = (int(y) * size + int(x)) * 4
        bg_r, bg_g, bg_b, bg_a = buf[idx], buf[idx+1], buf[idx+2], buf[idx+3] / 255.0
        alpha = a / 255.0
        out_a = alpha + bg_a * (1.0 - alpha)
        if out_a > 0:
            out_r = (r * alpha + bg_r * bg_a * (1.0 - alpha)) / out_a
            out_g = (g * alpha + bg_g * bg_a * (1.0 - alpha)) / out_a
            out_b = (b * alpha + bg_b * bg_a * (1.0 - alpha)) / out_a
            buf[idx] = int(round(out_r))
            buf[idx+1] = int(round(out_g))
            buf[idx+2] = int(round(out_b))
            buf[idx+3] = int(round(out_a * 255))

    # Fill background with gradient
    corner_r = 0 if full_square else 120 * scale
    for y in range(size):
        t = y / float(size)
        # Gradient from #6366f1 (99, 102, 241) to #ec4899 (236, 72, 153)
        gr_r = int(99 + (236 - 99) * t)
        gr_g = int(102 + (72 - 102) * t)
        gr_b = int(241 + (153 - 241) * t)
        for x in range(size):
            if full_square:
                blend(x, y, gr_r, gr_g, gr_b, 255)
            else:
                # check distance to rounded corner
                dx = max(0, abs(x - size/2) - (size/2 - corner_r))
                dy = max(0, abs(y - size/2) - (size/2 - corner_r))
                dist = math.sqrt(dx*dx + dy*dy)
                if dist <= corner_r:
                    alpha = 255
                    if dist > corner_r - 1.2:
                        alpha = int(255 * max(0.0, corner_r - dist) / 1.2)
                    blend(x, y, gr_r, gr_g, gr_b, alpha)

    def draw_circle(cx, cy, r, r_c, g_c, b_c, a_c=255):
        cx, cy, r = cx * scale, cy * scale, r * scale
        x0, x1 = max(0, int(cx - r - 2)), min(size, int(cx + r + 3))
        y0, y1 = max(0, int(cy - r - 2)), min(size, int(cy + r + 3))
        for y in range(y0, y1):
            for x in range(x0, x1):
                d = math.hypot(x - cx, y - cy)
                if d <= r:
                    alpha = a_c
                    if d > r - 1.2:
                        alpha = int(a_c * max(0.0, r - d) / 1.2)
                    blend(x, y, r_c, g_c, b_c, alpha)

    def draw_ellipse(cx, cy, rx, ry, r_c, g_c, b_c, a_c=255):
        cx, cy, rx, ry = cx * scale, cy * scale, rx * scale, ry * scale
        x0, x1 = max(0, int(cx - rx - 2)), min(size, int(cx + rx + 3))
        y0, y1 = max(0, int(cy - ry - 2)), min(size, int(cy + ry + 3))
        for y in range(y0, y1):
            for x in range(x0, x1):
                d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                if d <= 1.0:
                    alpha = a_c
                    if d > 0.85:
                        alpha = int(a_c * max(0.0, (1.0 - d) / 0.15))
                    blend(x, y, r_c, g_c, b_c, alpha)

    def draw_poly(pts, r_c, g_c, b_c, a_c=255):
        s_pts = [(p[0] * scale, p[1] * scale) for p in pts]
        min_x = max(0, int(min(p[0] for p in s_pts) - 1))
        max_x = min(size, int(max(p[0] for p in s_pts) + 2))
        min_y = max(0, int(min(p[1] for p in s_pts) - 1))
        max_y = min(size, int(max(p[1] for p in s_pts) + 2))
        n = len(s_pts)
        for y in range(min_y, max_y):
            py = y + 0.5
            for x in range(min_x, max_x):
                px = x + 0.5
                inside = False
                p1x, p1y = s_pts[0]
                for i in range(n + 1):
                    p2x, p2y = s_pts[i % n]
                    if py > min(p1y, p2y) and py <= max(p1y, p2y) and px <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (py - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                            if p1x == p2x or px <= xinters:
                                inside = not inside
                    p1x, p1y = p2x, p2y
                if inside:
                    blend(x, y, r_c, g_c, b_c, a_c)

    # Cat Ears outer
    draw_poly([(130, 250), (120, 140), (210, 200)], 255, 255, 255)
    draw_poly([(382, 250), (392, 140), (302, 200)], 255, 255, 255)
    # Cat Ears inner pink
    draw_poly([(142, 230), (132, 155), (195, 200)], 244, 114, 182)
    draw_poly([(370, 230), (380, 155), (317, 200)], 244, 114, 182)

    # Head and Body
    draw_ellipse(256, 275, 140, 115, 255, 255, 255)
    draw_poly([(150, 360), (362, 360), (385, 450), (127, 450)], 255, 255, 255)

    # Cheeks
    draw_ellipse(160, 285, 20, 12, 252, 165, 165, 160)
    draw_ellipse(352, 285, 20, 12, 252, 165, 165, 160)

    # Eyes
    draw_ellipse(195, 255, 18, 24, 30, 27, 75)
    draw_ellipse(317, 255, 18, 24, 30, 27, 75)
    # Highlights
    draw_ellipse(190, 247, 7, 9, 255, 255, 255)
    draw_ellipse(201, 263, 3, 4, 255, 255, 255)
    draw_ellipse(312, 247, 7, 9, 255, 255, 255)
    draw_ellipse(323, 263, 3, 4, 255, 255, 255)

    # Nose
    draw_poly([(246, 266), (266, 266), (256, 276)], 244, 63, 94)

    # Paw emblem on chest
    draw_circle(256, 395, 38, 124, 58, 237)
    draw_ellipse(256, 403, 18, 14, 255, 255, 255)
    draw_ellipse(240, 385, 6, 8, 255, 255, 255)
    draw_ellipse(250, 377, 6, 9, 255, 255, 255)
    draw_ellipse(262, 377, 6, 9, 255, 255, 255)
    draw_ellipse(272, 385, 6, 8, 255, 255, 255)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    write_png(out_path, size, size, buf)
    print(f"Generated {out_path} ({size}x{size}, full_square={full_square})")

if __name__ == '__main__':
    # Apple Touch Icon: 180x180 full square (no transparent corners, iOS handles rounding)
    generate_icon(180, 'd:/Web catdrop/apple-touch-icon.png', full_square=True)
    generate_icon(180, 'd:/Web catdrop/icons/apple-touch-icon.png', full_square=True)
    
    # Standard PWA icons (with squircle corner)
    generate_icon(192, 'd:/Web catdrop/icons/icon-192.png', full_square=False)
    generate_icon(512, 'd:/Web catdrop/icons/icon-512.png', full_square=False)
