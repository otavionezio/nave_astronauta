"""
Renderiza quadros em instantes escolhidos da sequência e salva PNGs (inspeção visual).
Uso:  python tests/render_frames.py [t1 t2 ...] [--size 1280x720] [--out tests/output]
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import headless_env

args = [a for a in sys.argv[1:]]
size, out = (1280, 720), os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
times = []
mode = None
cam = None
i = 0
while i < len(args):
    if args[i] == "--size":
        size = tuple(int(v) for v in args[i + 1].split("x")); i += 2
    elif args[i] == "--out":
        out = args[i + 1]; i += 2
    elif args[i] == "--mode":
        mode = args[i + 1]; i += 2
    elif args[i] == "--cam":          # az,el,dist,tx,ty,tz (graus, metros): câmera livre
        cam = [float(v) for v in args[i + 1].split(",")]; i += 2
    else:
        times.append(float(args[i])); i += 1
times = times or [0.5, 7.0, 12.0, 17.0, 20.0, 27.0]

real = headless_env.setup(*size)
print("bibliotecas reais:", real)
from app import Application, Options
os.makedirs(out, exist_ok=True)

t0 = time.time()
app = Application(size, Options())
print("Application criada em %.2f s | partes: astronauta=%d nave=%d" % (
    time.time() - t0, app.astronaut.partCount, app.ship.partCount))

if mode:
    app.update(0.0, headless_env.FakeInput(down={mode}))
if cam:
    import math
    o = app.orbit
    o.mode = "livre"
    o.azT, o.elT, o.distT = math.radians(cam[0]), math.radians(cam[1]), cam[2]
    o.anchor = [cam[3], cam[4], cam[5]]
    o.pan = [0.0, 0.0, 0.0]
    app.hud.visible = False
dt = 1 / 60
for target in sorted(times):
    while app.director.totalTime + 1e-9 < target:
        app.update(min(dt, target - app.director.totalTime), headless_env.FakeInput())
    app.update(0.0, headless_env.FakeInput())
    for _ in range(3):                                     # deixa a câmera suavizada convergir
        app.orbit.update(1.0, headless_env.FakeInput(), app._followPoints())
    t1 = time.time()
    app.render()
    img = headless_env.readFramebuffer(*size)
    tag = ("_m" + mode) if mode else ("_cam" if cam else "")
    path = os.path.join(out, "frame%s_%05.1f.png" % (tag, target))
    img.save(path)
    print("t=%5.1f s  estado=%-22s render=%.2f s draws=%d -> %s" % (
        target, app.director.state.name, time.time() - t1, app.mainDrawCalls, os.path.basename(path)))
