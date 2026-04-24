"""
frontend/hero.py
Full-screen hero landing page rendered before the dashboard.
Uses Three.js (r134 CDN) for the 3D neural-network background,
GSAP for text entrance animations, and a Barba.js-style page-wipe
transition into the dashboard when the user clicks "Launch".
"""
import streamlit as st
import streamlit.components.v1 as components


# Full self-contained HTML document rendered inside an iframe via components.html
HERO_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>EquiGuard</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@300;400&display=swap" rel="stylesheet">
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #06080f; overflow: hidden; }
/* iframe fills full parent */
html, body { width: 100%; height: 100%; }

/* ── Hero shell ──────────────────────────────────────────────────────── */
#eq-hero {
    position: relative;
    width: 100%;
    height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    background: #06080f;
}
#eq-hero-canvas {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
}
/* Dot-grid background */
#eq-hero::before {
    content: '';
    position: absolute;
    inset: 0;
    background-image:
        linear-gradient(rgba(99,102,241,0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(99,102,241,0.04) 1px, transparent 1px);
    background-size: 44px 44px;
    pointer-events: none;
}
/* Radial indigo glow */
#eq-hero::after {
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(ellipse 60% 70% at 65% 50%,
        rgba(99,102,241,0.10) 0%, transparent 70%);
    pointer-events: none;
}
/* Noise grain texture */
#eq-hero-noise {
    position: absolute;
    inset: 0;
    opacity: 0.025;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 512 512' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
    pointer-events: none;
}

/* ── Page-wipe overlay ───────────────────────────────────────────────── */
#eq-hero-wipe {
    position: fixed;
    inset: 0;
    z-index: 99999;
    background: linear-gradient(135deg, #6366f1 0%, #4338ca 60%, #1e1b4b 100%);
    clip-path: circle(0% at 50% 50%);
    pointer-events: none;
    transition: clip-path 0.55s cubic-bezier(0.76, 0, 0.24, 1);
}
#eq-hero-wipe.go { clip-path: circle(150% at 50% 50%); pointer-events: all; }

/* ── Content styles ──────────────────────────────────────────────────── */

.content {
    position: relative;
    z-index: 10;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
}

.shield-wrap {
    position: relative;
    width: 96px;
    height: 96px;
    margin-bottom: 1.75rem;
}

.shield-ring {
    position: absolute;
    inset: -18px;
    border-radius: 50%;
    border: 1px solid rgba(99,102,241,0.25);
    animation: ring-pulse 3s ease-in-out infinite;
}
.shield-ring:nth-child(2) {
    inset: -34px;
    border-color: rgba(99,102,241,0.12);
    animation-delay: 0.6s;
}
.shield-ring:nth-child(3) {
    inset: -52px;
    border-color: rgba(99,102,241,0.06);
    animation-delay: 1.2s;
}

@keyframes ring-pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(1.04); }
}

.shield-svg {
    width: 96px;
    height: 96px;
    position: relative;
    z-index: 2;
}

@keyframes shield-glow {
    0%, 100% { opacity: 0.8; }
    50% { opacity: 1; }
}

.eyeguard-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(99,102,241,0.12);
    border: 1px solid rgba(99,102,241,0.3);
    border-radius: 99px;
    padding: 4px 12px;
    margin-bottom: 1rem;
    animation: fade-up 0.6s ease both;
}
.badge-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #818cf8;
    animation: blink 2s ease-in-out infinite;
}
@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}
.badge-text {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 400;
    color: #818cf8;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 48px;
    font-weight: 700;
    line-height: 1.05;
    letter-spacing: -0.03em;
    color: #f0f1f5;
    margin-bottom: 0.15em;
    animation: fade-up 0.7s ease 0.1s both;
}
.hero-title span {
    color: #818cf8;
}

.hero-sub {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 15px;
    font-weight: 400;
    color: #4b5280;
    letter-spacing: 0.02em;
    margin-bottom: 2rem;
    animation: fade-up 0.7s ease 0.2s both;
}

@keyframes fade-up {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
}

.metrics-row {
    display: flex;
    gap: 10px;
    margin-bottom: 2rem;
    animation: fade-up 0.7s ease 0.3s both;
}

.metric-chip {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 10px 16px;
    text-align: center;
    min-width: 88px;
}
.metric-val {
    font-family: 'JetBrains Mono', monospace;
    font-size: 20px;
    font-weight: 400;
    color: #f0f1f5;
    line-height: 1;
    margin-bottom: 4px;
}
.metric-val.pass { color: #4ade80; }
.metric-val.fail { color: #f87171; }
.metric-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #3a3d52;
}

.audit-stream {
    width: 100%;
    max-width: 440px;
    animation: fade-up 0.7s ease 0.4s both;
}

.stream-line {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 5px 12px;
    border-radius: 6px;
    margin-bottom: 4px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    opacity: 0;
}
.stream-line.show { animation: line-in 0.3s ease forwards; }

@keyframes line-in {
    from { opacity: 0; transform: translateX(-6px); }
    to { opacity: 1; transform: translateX(0); }
}

.sl-dot { width: 5px; height: 5px; border-radius: 50%; flex-shrink: 0; }
.sl-ok { color: #4ade80; }
.sl-ok .sl-dot { background: #4ade80; }
.sl-warn { color: #fbbf24; }
.sl-warn .sl-dot { background: #fbbf24; }
.sl-err { color: #f87171; }
.sl-err .sl-dot { background: #f87171; }
.sl-info { color: #818cf8; }
.sl-info .sl-dot { background: #818cf8; }
.sl-muted { color: #2a2d40; }
.sl-muted .sl-dot { background: #2a2d40; }

.sl-bg-ok   { background: rgba(74,222,128,0.05); }
.sl-bg-warn { background: rgba(251,191,36,0.05); }
.sl-bg-err  { background: rgba(248,113,113,0.05); }
.sl-bg-info { background: rgba(129,140,248,0.05); }

.sl-key { color: #3a3d52; margin-right: 2px; }
.eeoc-bar {
    height: 3px;
    border-radius: 99px;
    background: rgba(255,255,255,0.05);
    overflow: hidden;
    margin-top: 6px;
}
.eeoc-fill {
    height: 100%;
    border-radius: 99px;
    width: 0%;
    transition: width 1.2s cubic-bezier(0.4,0,0.2,1);
}

.cta-row {
    display: flex;
    gap: 10px;
    margin-top: 1.75rem;
    animation: fade-up 0.7s ease 0.5s both;
    position: relative;
    z-index: 20;
}
.btn-primary {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 13px;
    font-weight: 500;
    padding: 9px 20px;
    border-radius: 8px;
    background: #534AB7;
    color: #EEEDFE;
    border: none;
    cursor: pointer;
    letter-spacing: 0.01em;
    transition: background 0.2s, transform 0.1s;
}
.btn-primary:hover { background: #3C3489; }
.btn-primary:active { transform: scale(0.98); }
.btn-ghost {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 13px;
    font-weight: 400;
    padding: 9px 20px;
    border-radius: 8px;
    background: transparent;
    color: #4b5280;
    border: 1px solid rgba(255,255,255,0.08);
    cursor: pointer;
    transition: color 0.2s, border-color 0.2s;
}
.btn-ghost:hover { color: #818cf8; border-color: rgba(129,140,248,0.3); }

.compliance-stamp {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    margin-top: 1.25rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 9.5px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #2a2d40;
    opacity: 0;
    animation: fade-up 0.5s ease 2.8s forwards;
}
.stamp-line { height: 1px; width: 28px; background: rgba(255,255,255,0.06); }
</style>

<div id="eq-hero-wipe"></div>
<div id="eq-hero">
    <div id="eq-hero-noise"></div>
    <canvas id="eq-hero-canvas"></canvas>

    <div class="content">
        <div class="eyeguard-badge">
            <div class="badge-dot"></div>
            <span class="badge-text">AI bias firewall · v1.0 · EEOC compliant</span>
        </div>

        <div class="shield-wrap">
            <div class="shield-ring"></div>
            <div class="shield-ring"></div>
            <div class="shield-ring"></div>
            <svg class="shield-svg" viewBox="0 0 96 96" fill="none" xmlns="http://www.w3.org/2000/svg" style="animation: shield-glow 2.5s ease-in-out infinite;">
                <path d="M48 8L14 22V46C14 64.6 29.1 82.1 48 87C66.9 82.1 82 64.6 82 46V22L48 8Z" fill="rgba(83,74,183,0.15)" stroke="#534AB7" stroke-width="1.5"/>
                <path d="M48 18L22 29V46C22 60.2 33.4 73.5 48 78C62.6 73.5 74 60.2 74 46V29L48 18Z" fill="rgba(83,74,183,0.1)" stroke="rgba(129,140,248,0.4)" stroke-width="0.8"/>
                <path d="M36 48L44 56L60 40" stroke="#818cf8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                <circle cx="48" cy="48" r="3" fill="#818cf8" opacity="0.4"/>
            </svg>
        </div>

        <div class="hero-title">Equi<span>Guard</span></div>
        <div class="hero-sub">Intercept bias before it reaches production</div>

        <div class="metrics-row">
            <div class="metric-chip">
                <div class="metric-val pass" id="m-ratio">—</div>
                <div class="metric-label">fairness ratio</div>
            </div>
            <div class="metric-chip">
                <div class="metric-val" id="m-status" style="font-size:13px;padding-top:3px;color:#3a3d52;">auditing...</div>
                <div class="metric-label">eeoc status</div>
            </div>
            <div class="metric-chip">
                <div class="metric-val" id="m-shap" style="color:#818cf8;">—</div>
                <div class="metric-label">top shap feature</div>
            </div>
        </div>

        <div class="audit-stream" id="auditStream"></div>

        <div class="eeoc-bar" style="width:100%;max-width:440px;margin-top:8px;">
            <div class="eeoc-fill" id="eeocFill" style="background:#534AB7;"></div>
        </div>

        <div class="cta-row">
            <button class="btn-primary" id="run-audit-btn">Run audit ↗</button>
            <button class="btn-ghost" onclick="window.open('https://github.com', '_blank')">View docs</button>
        </div>

        <div class="compliance-stamp">
            <div class="stamp-line"></div>
            29 CFR § 1607 · 4/5ths rule · SHAP explainability · aif360
            <div class="stamp-line"></div>
        </div>
    </div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r134/three.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>

<script>
(function () {
    /* ── Reset the wipe overlay immediately on load (prevents stale animation) */
    document.addEventListener('DOMContentLoaded', function() {
        const wipe = document.getElementById('eq-hero-wipe');
        if (wipe) {
            wipe.classList.remove('go');
            wipe.style.transition = 'none';
            // Re-enable transition on next frame
            requestAnimationFrame(() => {
                wipe.style.transition = '';
            });
        }
    });

    /* ── Wait for Three.js + page fully loaded ───────────────────────── */
    function waitFor(fn, cb, n) {
        if (fn()) { cb(); }
        else if ((n || 0) < 40) { setTimeout(() => waitFor(fn, cb, (n||0)+1), 150); }
    }

    // Defer init until window is fully loaded so canvas has correct dimensions
    function initHero() {
        waitFor(() => window.THREE, function () {

        /* ── Three.js scene ──────────────────────────────────────────── */
        const canvas = document.getElementById('eq-hero-canvas');
        if (!canvas) return;

        // Use window dimensions — canvas is position:absolute filling #eq-hero
        const W = window.innerWidth  || document.documentElement.clientWidth;
        const H = window.innerHeight || document.documentElement.clientHeight;

        const scene    = new THREE.Scene();
        const camera   = new THREE.PerspectiveCamera(55, W / H, 0.1, 100);
        camera.position.set(0, 0, 9);

        const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
        renderer.setSize(W, H);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.setClearColor(0x000000, 0);

        /* ── Central icosahedron shell (wireframe brain) ─────────────── */
        const icoGeo = new THREE.IcosahedronGeometry(2.2, 2);
        const icoMat = new THREE.MeshPhongMaterial({
            color: 0x6366f1, wireframe: true,
            transparent: true, opacity: 0.10
        });
        const ico = new THREE.Mesh(icoGeo, icoMat);
        ico.position.set(0, 0, -2);
        scene.add(ico);

        /* ── Inner glow ──────────────────────────────────────────────── */
        const glowGeo = new THREE.SphereGeometry(1.8, 32, 32);
        const glowMat = new THREE.MeshBasicMaterial({
            color: 0x4338ca, transparent: true, opacity: 0.04
        });
        const glowMesh = new THREE.Mesh(glowGeo, glowMat);
        glowMesh.position.set(0, 0, -2);
        scene.add(glowMesh);

        /* ── Floating particles (neural nodes) ───────────────────────── */
        const N   = 220;
        const pos = new Float32Array(N * 3);
        const vel = [];
        for (let i = 0; i < N; i++) {
            pos[i*3]   = (Math.random() - 0.5) * 14;
            pos[i*3+1] = (Math.random() - 0.5) * 10;
            pos[i*3+2] = (Math.random() - 0.5) * 5 - 1;
            vel.push({
                x: (Math.random() - 0.5) * 0.006,
                y: (Math.random() - 0.5) * 0.006,
                z: (Math.random() - 0.5) * 0.003
            });
        }
        const pGeo  = new THREE.BufferGeometry();
        const pAttr = new THREE.BufferAttribute(pos, 3);
        pGeo.setAttribute('position', pAttr);
        const pMat = new THREE.PointsMaterial({
            color: 0x818cf8, size: 0.045,
            transparent: true, opacity: 0.85
        });
        scene.add(new THREE.Points(pGeo, pMat));

        /* ── Dynamic connection lines ────────────────────────────────── */
        const MAX_LINES = 600;
        const lPos  = new Float32Array(MAX_LINES * 6);
        const lGeo  = new THREE.BufferGeometry();
        const lAttr = new THREE.BufferAttribute(lPos, 3);
        lGeo.setAttribute('position', lAttr);
        lGeo.setDrawRange(0, 0);
        scene.add(new THREE.LineSegments(
            lGeo,
            new THREE.LineBasicMaterial({
                color: 0x6366f1, transparent: true, opacity: 0.10
            })
        ));

        /* ── Orbiting torus rings ─────────────────────────────────────── */
        function addRing(r, tiltX, tiltY, color) {
            const g = new THREE.TorusGeometry(r, 0.009, 8, 120);
            const m = new THREE.MeshBasicMaterial({
                color, transparent: true, opacity: 0.20
            });
            const mesh = new THREE.Mesh(g, m);
            mesh.position.set(0, 0, -2);
            mesh.rotation.x = tiltX;
            mesh.rotation.y = tiltY;
            scene.add(mesh);
            return mesh;
        }
        const ring1 = addRing(2.8,  Math.PI/2.2,  0.4,  0x6366f1);
        const ring2 = addRing(3.5,  0.7,  Math.PI/4,   0x38bdf8);
        const ring3 = addRing(2.2, -0.6,  Math.PI/5,   0xa5b4fc);

        /* ── Lights ──────────────────────────────────────────────────── */
        scene.add(new THREE.AmbientLight(0x6366f1, 0.6));
        const pl1 = new THREE.PointLight(0x818cf8, 2.5, 25);
        pl1.position.set(6, 4, 4);
        scene.add(pl1);
        const pl2 = new THREE.PointLight(0x38bdf8, 1.5, 20);
        pl2.position.set(-4, -3, 3);
        scene.add(pl2);

        /* ── Mouse parallax ──────────────────────────────────────────── */
        let mx = 0, my = 0;
        window.addEventListener('mousemove', e => {
            mx = (e.clientX / window.innerWidth  - 0.5) * 2;
            my = (e.clientY / window.innerHeight - 0.5) * 2;
        });

        /* ── Animation loop ──────────────────────────────────────────── */
        let t = 0;
        function animate() {
            requestAnimationFrame(animate);
            t += 0.006;

            /* Move particles */
            for (let i = 0; i < N; i++) {
                pos[i*3]   += vel[i].x;
                pos[i*3+1] += vel[i].y;
                pos[i*3+2] += vel[i].z;
                if (Math.abs(pos[i*3])   > 7)  vel[i].x *= -1;
                if (Math.abs(pos[i*3+1]) > 5)  vel[i].y *= -1;
                if (Math.abs(pos[i*3+2]) > 2.5) vel[i].z *= -1;
            }
            pAttr.needsUpdate = true;

            /* Rebuild connection lines */
            let lc = 0;
            for (let i = 0; i < N && lc < MAX_LINES; i++) {
                for (let j = i+1; j < N && lc < MAX_LINES; j++) {
                    const dx = pos[i*3]-pos[j*3],
                          dy = pos[i*3+1]-pos[j*3+1],
                          dz = pos[i*3+2]-pos[j*3+2];
                    const d = Math.sqrt(dx*dx+dy*dy+dz*dz);
                    if (d < 1.6) {
                        lPos[lc*6]   = pos[i*3];   lPos[lc*6+1] = pos[i*3+1]; lPos[lc*6+2] = pos[i*3+2];
                        lPos[lc*6+3] = pos[j*3];   lPos[lc*6+4] = pos[j*3+1]; lPos[lc*6+5] = pos[j*3+2];
                        lc++;
                    }
                }
            }
            lAttr.needsUpdate = true;
            lGeo.setDrawRange(0, lc * 2);

            /* Rotate 3D object */
            ico.rotation.y = t * 0.4;
            ico.rotation.x = t * 0.15;
            glowMesh.rotation.y = t * 0.3;

            /* Rings */
            ring1.rotation.z += 0.005;
            ring2.rotation.z -= 0.004;
            ring3.rotation.y += 0.006;

            /* Pulse glow */
            const pulse = Math.sin(t * 1.8) * 0.03 + 1;
            glowMesh.scale.setScalar(pulse);

            /* Camera parallax */
            camera.position.x += (mx * 0.8 - camera.position.x) * 0.05;
            camera.position.y += (-my * 0.5 - camera.position.y) * 0.05;
            camera.lookAt(0, 0, -2);

            renderer.render(scene, camera);
        }
        animate();

        /* ── Resize ──────────────────────────────────────────────────── */
        window.addEventListener('resize', () => {
            const nW = window.innerWidth;
            const nH = window.innerHeight;
            camera.aspect = nW / nH;
            camera.updateProjectionMatrix();
            renderer.setSize(nW, nH);
        });

    }); /* end waitFor */
    } /* end initHero */

    if (document.readyState === 'complete') {
        initHero();
    } else {
        window.addEventListener('load', initHero);
    }

    /* ── Audit Stream Animation ───────────────────────────────────── */
    const auditLines = [
      { type: 'info',  text: '→ loading dataset · golden_demo_dataset.csv',   delay: 600  },
      { type: 'muted', text: '  rows: 5278  ·  features: 8  ·  target: loan_approved', delay: 900 },
      { type: 'info',  text: '→ training logistic regression pipeline…',       delay: 1300 },
      { type: 'ok',    text: '✓ pipeline trained  ·  accuracy: 0.8341',        delay: 1800 },
      { type: 'info',  text: '→ running proxy hunter (feature agglomeration)',  delay: 2100 },
      { type: 'warn',  text: '⚠ flagged: zip_code  ·  |r| = 0.61  proxy detected', delay: 2500 },
      { type: 'info',  text: '→ computing SHAP (LinearExplainer)…',            delay: 2900 },
      { type: 'ok',    text: '✓ top feature: zip_code  ·  mean|SHAP|: 0.183', delay: 3300 },
      { type: 'info',  text: '→ EEOC 4/5ths audit (29 CFR § 1607)…',          delay: 3700 },
      { type: 'ok',    text: '✓ ratio: 0.8412  ·  threshold: 0.80  ·  PASS',  delay: 4200 },
    ];

    const stream = document.getElementById('auditStream');

    function makeLineEl(line) {
      const el = document.createElement('div');
      el.className = `stream-line sl-${line.type} sl-bg-${line.type === 'muted' ? 'info' : line.type}`;
      const dot = document.createElement('div');
      dot.className = 'sl-dot';
      const txt = document.createElement('span');
      txt.textContent = line.text;
      el.appendChild(dot);
      el.appendChild(txt);
      return el;
    }

    function runAuditAnimation() {
      if (!stream) return;
      auditLines.forEach(line => {
        setTimeout(() => {
          const el = makeLineEl(line);
          stream.appendChild(el);
          requestAnimationFrame(() => el.classList.add('show'));
          if (stream.children.length > 5) stream.removeChild(stream.firstChild);
        }, line.delay);
      });

      setTimeout(() => {
        document.getElementById('m-ratio').textContent = '0.84';
        document.getElementById('m-ratio').className = 'metric-val pass';
      }, 4300);
      setTimeout(() => {
        const s = document.getElementById('m-status');
        s.textContent = 'PASS';
        s.style.color = '#4ade80';
        s.style.fontSize = '18px';
      }, 4400);
      setTimeout(() => {
        document.getElementById('m-shap').textContent = 'zip';
      }, 3400);
      setTimeout(() => {
        document.getElementById('eeocFill').style.width = '84%';
        document.getElementById('eeocFill').style.background = '#4ade80';
      }, 4500);
    }

    function restartCycle() {
      setTimeout(() => {
        document.getElementById('m-ratio').textContent = '—';
        document.getElementById('m-ratio').className = 'metric-val pass';
        document.getElementById('m-status').textContent = 'auditing...';
        document.getElementById('m-status').style.color = '#3a3d52';
        document.getElementById('m-status').style.fontSize = '13px';
        document.getElementById('m-shap').textContent = '—';
        document.getElementById('eeocFill').style.width = '0%';
        document.getElementById('eeocFill').style.transition = 'none';
        if (stream) {
            while (stream.firstChild) stream.removeChild(stream.firstChild);
        }
        setTimeout(() => {
          document.getElementById('eeocFill').style.transition = 'width 1.2s cubic-bezier(0.4,0,0.2,1)';
          runAuditAnimation();
          setTimeout(restartCycle, 4600);
        }, 200);
      }, 8000);
    }

    runAuditAnimation();
    setTimeout(restartCycle, 4600);

    /* ── Page-wipe trigger (called by Streamlit button via JS) ───────── */
    window._heroLaunch = function () {
        const wipe = document.getElementById('eq-hero-wipe');
        if (wipe) wipe.classList.add('go');
    };

    /* ── Click handler ────────────────────────────────────────────── */
    const runBtn = document.getElementById('run-audit-btn');
    if (runBtn) {
        runBtn.addEventListener('click', () => {
            // 1) Play the wipe animation
            const wipe = document.getElementById('eq-hero-wipe');
            if (wipe) wipe.classList.add('go');

            // 2) After animation, directly click the hidden Streamlit button.
            //    The iframe is same-origin (localhost:8501), and Streamlit sets
            //    sandbox="allow-same-origin" so window.parent.document is accessible.
            setTimeout(() => {
                try {
                    const parentDoc = window.parent.document;
                    const allBtns = parentDoc.querySelectorAll('button');
                    for (let i = 0; i < allBtns.length; i++) {
                        if (allBtns[i].innerText.trim() === '__hero_launch__') {
                            allBtns[i].click();
                            return;
                        }
                    }
                    // Fallback: click any button with data-testid stBaseButton
                    const fb = parentDoc.querySelector('[data-testid="stBaseButton-secondary"]');
                    if (fb) fb.click();
                } catch (err) {
                    console.warn('EquiGuard: could not reach parent DOM', err);
                }
            }, 520);
        });
    }

})();
</script>
</body>
</html>"""

def render_hero():
    """
    Renders the full-screen hero landing page inside a full-viewport iframe.

    Communication flow:
      iframe JS (same-origin) → window.parent.document.querySelector('button').click()
      → hidden Streamlit button → session_state.hero_dismissed = True → st.rerun()
    """
    # ── 1) CSS: hide chrome, dark bg, stretch iframe ──────────────────────────
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"],
        [data-testid="stSidebarNav"],
        header, footer, #MainMenu { display: none !important; }

        html, body, .stApp, [data-testid="stAppViewContainer"],
        [data-testid="stMain"], .block-container,
        [data-testid="stVerticalBlock"] {
            padding: 0 !important;
            margin: 0 !important;
            max-width: 100vw !important;
            width: 100vw !important;
            background: #06080f !important;
        }
        html, body { height: 100vh !important; overflow: hidden !important; }
        .stApp      { height: 100vh !important; overflow: hidden !important; }

        /* Stretch the components iframe to fill the entire viewport */
        iframe {
            border: none !important;
            display: block !important;
            width: 100vw !important;
            min-height: 100vh !important;
            position: fixed !important;
            inset: 0 !important;
            z-index: 9999 !important;
        }

        /* Visually hide the Streamlit trigger button but keep it in the DOM */
        #hero-launch-hidden-wrap,
        #hero-launch-hidden-wrap * {
            position: fixed !important;
            top: -999px !important;
            left: -999px !important;
            width: 1px !important;
            height: 1px !important;
            opacity: 0 !important;
            pointer-events: none !important;
            overflow: hidden !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ── 2) Hidden Streamlit button — must exist in DOM BEFORE the iframe renders ──
    #    The iframe JS finds it via window.parent.document.querySelectorAll('button')
    st.markdown('<div id="hero-launch-hidden-wrap">', unsafe_allow_html=True)
    clicked = st.button("__hero_launch__", key="hero_cta")
    st.markdown('</div>', unsafe_allow_html=True)

    if clicked:
        st.session_state.hero_dismissed = True
        st.rerun()

    # ── 3) Hero iframe ─────────────────────────────────────────────────────────────
    #    height=10000 allocates space; position:fixed CSS pins it to 100vh.
    components.html(HERO_HTML, height=10000, scrolling=False)
