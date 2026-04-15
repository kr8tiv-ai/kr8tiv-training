# Awwwards — Real Code Snippets, Per Library

Auto-extracted from the 96 SOTD winners we scraped. Each snippet is a ~600-char context window around a canonical library API call, sourced from the live site's HTML or linked CSS/JS.

Use these as few-shot examples when Cipher generates. They're the *actual* patterns that win Awwwards.

## GLSL  (2 snippets from 1 sites — showing top 2)

### `darknode`

```js
pt>

<script type="module">

// === 💡 ПОЧАТОК ПЕРЕВІРКИ ===
// Запускаємо, якщо ширина вікна більша за 991px (стандартний брейкпоінт Webflow для планшета)
if (window.innerWidth > 991) {

var vertex = `
varying vec2 vUv;
varying vec3 vPosition;
uniform vec2 pixels;
float PI = 3.141592653589793238;
void main() {
  vUv = uv;
  gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
}`;

var fragment = `
  uniform float progress;
  uniform sampler2D uDataTexture;
  uniform sampler2D uTexture;

uniform vec4 resolution;
  varying vec2 vUv;
  varying vec3 vPosition;
  float PI = 3.1 /* ... */
```

### `darknode`

```js
ition = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
}`;

var fragment = `
  uniform float progress;
  uniform sampler2D uDataTexture;
  uniform sampler2D uTexture;

uniform vec4 resolution;
  varying vec2 vUv;
  varying vec3 vPosition;
  float PI = 3.141592653589793238;
  void main()	{
  vec2 newUV = (vUv - vec2(0.5)) * resolution.zw + vec2(0.5);
  vec4 color = texture2D(uTexture,newUV);
  vec4 offset = texture2D(uDataTexture,vUv);
  gl_FragColor = vec4(vUv,0.0,1.);
  gl_FragColor = vec4(offset.r,0.,0.,1.);
  gl_FragColor = color;
  gl_FragColor = texture2D(uTexture,newUV - 0.0 /* ... */
```

## GSAP  (24 snippets from 10 sites — showing top 6)

### `artem-shcherban-portfolio`

```js
rray(items);
  config = config || {};
  gsap.context(() => { // use a context so that if this is called from within another context or a gsap.matchMedia(), we can perform proper cleanup like the "resize" event handler on the window
  let onChange = config.onChange,
  lastIndex = 0,
  tl = gsap.timeline({repeat: config.repeat, onUpdate: onChange && function() {
  let i = tl.closestIndex();
  if (lastIndex !== i) {
  lastIndex = i;
  onChange(items[i], i);
  }
  }, paused: config.paused, defaults: {ease: "none"}, onReverseComplete: () => tl.totalTime(tl.rawTime() + tl.duration() * 100)}),
  leng /* ... */
```

### `ava-srg`

```js
.length === 0) { resolve(); return; }

// Ждем выполнения всех обещаний

Promise.all(mediaPromises).then(() => setTimeout(resolve, 100));

});

}

// --- 2. АНИМАЦИЯ ЦИФР ---

function animateCounter(element, duration) {

const counterObject = { value: 0 };

return gsap.to(counterObject, {

value: 100,

duration: duration,

ease: "expoScale(0.5,7,none)",

onUpdate: function() {

element.textContent = Math.round(counterObject.value) + "%";

}

});

}

// --- 3. ГЛАВНАЯ ФУНКЦИЯ ---

function initPreloader() {

// === НАСТРОЙКИ ===

const my3dClass = '.hand'; // <-- ВАШ КЛАСС

const screensToChec /* ... */
```

### `c-design-by-dylan`

```js
(onDone) => {
  showOverlay();

if (prefersReduced) {
  gsap.set(allCols, { scaleX: 1 });
  onDone && onDone();
  return;
  }

const cols = getActiveCols();

// Zorg dat grid overlay weer zichtbaar is tijdens cover-in
  gsap.set(".divs.is-pt", { opacity: 0.15 });

gsap.fromTo(
  cols,
  { scaleX: 0, transformOrigin: "left" },
  {
  scaleX: 1,
  duration: 0.55,
  ease: "power4.inOut",
  stagger: { each: 0.06, from: "start" },
  onComplete: () => onDone && onDone()
  }
  );
  };

// Run reveal after alles geladen is
  window.addEventListener("load", revealOut);

// BFCACHE fix (Safari back/forwa /* ... */
```

### `darknode`

```js
}

// 2. ПРИСВОЮЄМО ЗНАЧЕННЯ ЗОВНІШНІЙ ЗМІННІЙ
            splitInstance = new SplitText(link, { type: "chars" });
            const chars = splitInstance.chars; // Використовуємо її
            const originalChars = chars.map(char => char.textContent);

currentAnimation = gsap.timeline();

chars.forEach((char, index) => {
                let proxy = { frame: 0 }; 
                currentAnimation.to(proxy, {
                    frame: 10,
                    duration: 0.15,
                    ease: "none",
                    onUpdate: () => {
                        char.textContent = getRa /* ... */
```

### `farm-minerals`

```js
mage(img, x, y, iw * scale, ih * scale);
}

// --- Перерисовка при ресайзе ---
window.addEventListener("resize", () => {
  setCanvasSize();
  drawFrame(Math.round(frameObj?.frame || 0));
});

let frameObj = { frame: 0 };

// --- ScrollTrigger-анимация ---
function startScroll() {
  drawFrame(0);

gsap.to(frameObj, {
  frame: total - 1,
  ease: "none",
  scrollTrigger: {
  trigger: ".capsule",
  start: "top top",
  end: "bottom bottom",
  scrub: 1
  },
  onUpdate: () => {
  const i = Math.round(frameObj.frame);
  drawFrame(i);
  }
  });
}
</script>

<script>
(() => {
  // Цвета
  const LIGHT =  /* ... */
```

### `nicola-romeitm`

```js
ding"]');e.forEach(e=>{gsap.set(e,{autoAlpha:1});let l=new SplitText(e,{type:"lines",linesClass:"mask-line"});l.lines.forEach(e=>{let l=document.createElement("div");for(l.style.display="block";e.firstChild;)l.appendChild(e.firstChild);e.appendChild(l)});let t=e.querySelectorAll(".mask-line > div");gsap.from(t,{yPercent:100,duration:.85,stagger:.05,ease:"power4.out",scrollTrigger:{trigger:e,start:"top 95%",toggleActions:"play none none none"}})})});
</script><script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/virtu /* ... */
```

## Lenis  (7 snippets from 6 sites — showing top 6)

### `artem-shcherban-portfolio`

```js
document.addEventListener("DOMContentLoaded", () => {
  const wrapper = document.querySelector("[data-lenis-wrapper]") ?? window;
  const content = document.querySelector("[data-lenis-content]") ?? document.body;
  const target = document.querySelector("[data-lenis-target]") ?? wrapper;

lenis = new Lenis({
  wrapper: wrapper,
  content: content,
  eventsTarget: target,

autoRaf: true,
  lerp: 0.1,
  })

// lenis.on('scroll', ScrollTrigger.update);

// gsap.ticker.add((time) => {
  //  lenis.raf(time * 1000);
  // });

// gsap.ticker.lagSmoothing(0);

const elements = document.querySelectorAll /* ... */
```

### `ava-srg`

```js
ent=` html.lenis,html.lenis body{height:auto;}.lenis.lenis-smooth{scroll-behavior:auto!important;}.lenis.lenis-smooth[data-lenis-prevent]{overscroll-behavior:contain;}.lenis.lenis-stopped{overflow:hidden;}.lenis.lenis-smooth iframe{pointer-events:none;}`;document.head.appendChild(style);const lenis=new Lenis({lerp:0.082,duration:1.2,wheelMultiplier:1.0,anchors:!0,gestureOrientation:'vertical',normalizeWheel:!1,smoothTouch:!1});document.documentElement.classList.add('lenis');function raf(time){lenis.raf(time);requestAnimationFrame(raf);}requestAnimationFrame(raf);window.lenis=lenis;};document.h /* ... */
```

### `champions-for-good`

```js
nextEl: ".button-next", prevEl: ".button-prev" },
  scrollbar: { el: ".swiper-scrollbar", draggable: true }
});
</script>

<script>
/* ============================================================
  LENIS SMOOTH SCROLL
  ============================================================ */
const lenis = new Lenis();

function raf(time) {
  lenis.raf(time);
  requestAnimationFrame(raf);
}
requestAnimationFrame(raf);
</script>
-->
</body></html>

html{-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%;font-family:sans-serif}body{margin:0}article,aside,details,figcaption,figure,footer,header,hgroup /* ... */
```

### `darknode`

```js
ay = 'block';
  vertical.style.display = 'block';
  horizontal.style.display = 'block';
  coords.style.display = 'flex';
  });

} // <-- Кінець умови if
</script>

<script src="https://unpkg.com/@studio-freight/lenis@1.0.33/dist/lenis.min.js"></script>
  <script>

window.lenis = new Lenis({
  // Value between 0 and 1
  // Default value: 0.1
  // The lower the value, the smoother the scroll
  lerp: 0.05, 
  // Default value: 1
  // The higher the value, the faster the scrolling
  wheelMultiplier: 1, 
});

function raf(time) {
  lenis.raf(time);
  requestAnimationFrame(raf);
}
requestAnimationFr /* ... */
```

### `farm-minerals`

```js
",
  },
  delay: delayValue,
  }
  );

createScrollTrigger(el, tl);
  });

gsap.set("[text-split], [text-split-delay]", { autoAlpha: 1 });
  });
</script>

<script src="https://unpkg.com/lenis@1.1.13/dist/lenis.min.js"></script>

<script>

window.lenis = new Lenis({
  lerp: 0.1,
});

window.lenis.on('scroll', (e) => {});

function raf(time) {
  window.lenis.raf(time);
  requestAnimationFrame(raf);
}
requestAnimationFrame(raf);

$("[data-lenis-start]").on("click", function () {
  window.lenis.start();
});
$("[data-lenis-stop]").on("click", function () {
  window.lenis.stop();
```

### `c-design-by-dylan`

```js
- blurStart) / (blurEnd - blurStart);
  opacity = 1 - localProgress;
  }

// apply styles
  heroText.style.filter = blur === 0 ? "none" : `blur(${blur}px)`;
  heroText.style.opacity = opacity; // 👈 deze ontbrak nog
  }
  },
  });

lenis = new Lenis({
  smooth: true,
  lerp: 0.1,
  smoothWheel: true,
  });

lenis.on("scroll", () => {
  ScrollTrigger.update();
  });

gsap.ticker.add((time) => {
  lenis.raf(time * 1000);
  });

gsap.ticker.lagSmoothing(0);

requestAnimationFrame(() => {
  ScrollTrigger.refresh();
  });
  }

// 🎯 RESIZE HANDLER - Destroy si on passe
```

## Locomotive  (1 snippets from 1 sites — showing top 1)

### `c-design-by-dylan`

```js
50);
});
</script>

<!-- Locomotive Scroll -->
<script>
let locomotiveScroll;

document.addEventListener("DOMContentLoaded", () => {
  const isDesktop = window.matchMedia("(min-width: 768px)").matches;

if (!isDesktop) {
  // No Locomotive on mobile/tablet
  return;
  }

locomotiveScroll = new LocomotiveScroll({
  lenisOptions: {
  lerp: 0.1,
  duration: 1.2,
  easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
  }
  });
});
</script>

<!-- Global Image Animations -->
<script>
// ================================
document.addEventListener("DOMContentLoaded", () => {
  const wrappers = gs /* ... */
```

## Lottie  (1 snippets from 1 sites — showing top 1)

### `ava-srg`

```js
ventListener('DOMContentLoaded', () => {

if (typeof lottie === 'undefined' || typeof gsap === 'undefined') {

console.warn('Lottie/GSAP not loaded');

return;

}

gsap.registerPlugin(ScrollTrigger);

const container = document.getElementById('lottie-container');

const anim = lottie.loadAnimation({

container,

path: '/f/logo.json',  // Проверьте путь!

renderer: 'svg',

autoplay: false,

loop: false

});

anim.addEventListener('data_ready', () => {  // Правильное событие

ScrollTrigger.create({

trigger: document.body,

start: 'top top',

end: 'bottom bottom',

scrub: true,

onUpdate: (self) /* ... */
```

## ScrollTrigger  (8 snippets from 4 sites — showing top 5)

### `ava-srg`

```js
=> { if (!isHoveringHandInFooter && isHandReady) safeChangeAnimation(3, 0.5); },

onEnterBack: () => { if (!isHoveringHandInFooter && isHandReady) safeChangeAnimation(3, 0.5); }

}

});

// ABOUT sHandReady

gsap.timeline({

scrollTrigger: {

trigger: '.about_section-cc',

start: 'top center',

end: 'bottom center',

onEnter: () => { if (!isHoveringHandInFooter && isHandReady) safeChangeAnimation(4, 0.5); },

onEnterBack: () => { if (!isHoveringHandInFooter && isHandReady) safeChangeAnimation(4, 0.5); }

}

});

// TEAM + isHandReady

const teamSection = document.querySelector('.team_section') /* ... */
```

### `c-design-by-dylan`

```js
mg, picture, video");

if (!media) return;

// Zet 'm eerst bewust op blur, dan pas animeren
  if (allowBlur) {
  gsap.set(media, { filter: "blur(16px)" });
  }

gsap.to(media, {
  filter: allowBlur ? "blur(0px)" : "none",
  duration: 1.1,
  ease: "power2.out",
  scrollTrigger: {
  trigger: wrapper,  // trigger op de link / card
  start: "top 85%",
  toggleActions: "play none none none"
  }
  });
  });
});
</script>

<!-- Mix Blend Mode -->
<script>
function applyMixBlendMode() {
  const isMobile = window.matchMedia("(max-width: 479px)").matches;

document.querySelectorAll("[data-mix-blend-mod /* ... */
```

### `c-design-by-dylan`

```js
.set(timeEl, { filter: "blur(0px)" });
  }
  }
  };

if (inViewOnLoad) {
  // Direct animeren als hij al in beeld is
  gsap.from(timeEl, baseConfig);
  } else {
  // ScrollTrigger als hij lager op de pagina staat
  gsap.from(timeEl, {
  ...baseConfig,
  scrollTrigger: {
  trigger: timeEl,
  start: "top 80%",
  toggleActions: "play none none none"
  }
  });
  }
  }

// 🧾 .rich-text-work content
  animateWithOptionalDelay(
  gsap.utils.toArray(".rich-text-work *"),
  "lines, words",
  {
  opacity: 1,
  filter: "blur(0px)",
  duration: 0.8,
  ease: "power2.out",
  stagger: 0.1
  }
  );
</script>
 /* ... */
```

### `farm-minerals`

```js
ри ресайзе ---
window.addEventListener("resize", () => {
  setCanvasSize();
  drawFrame(Math.round(frameObj?.frame || 0));
});

let frameObj = { frame: 0 };

// --- ScrollTrigger-анимация ---
function startScroll() {
  drawFrame(0);

gsap.to(frameObj, {
  frame: total - 1,
  ease: "none",
  scrollTrigger: {
  trigger: ".capsule",
  start: "top top",
  end: "bottom bottom",
  scrub: 1
  },
  onUpdate: () => {
  const i = Math.round(frameObj.frame);
  drawFrame(i);
  }
  });
}
</script>

<script>
(() => {
  // Цвета
  const LIGHT = '#F4EDE6';
  const DARK  = '#404F1D';

// Целевые секции
  const /* ... */
```

### `nicola-romeitm`

```js
e,{type:"lines",linesClass:"mask-line"});l.lines.forEach(e=>{let l=document.createElement("div");for(l.style.display="block";e.firstChild;)l.appendChild(e.firstChild);e.appendChild(l)});let t=e.querySelectorAll(".mask-line > div");gsap.from(t,{yPercent:100,duration:.85,stagger:.05,ease:"power4.out",scrollTrigger:{trigger:e,start:"top 95%",toggleActions:"play none none none"}})})});
</script><script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/virtual-scroll@2.1.1/lib/virtualscroll.min.js"></script>
<script src="http /* ... */
```

## SplitText  (15 snippets from 7 sites — showing top 6)

### `ava-srg`

```js
Popup() {
  lockScroll();

gsap.set(popup, { display: 'flex' });
  gsap.set(popupContent, { 
  scaleY: 0, 
  transformOrigin: 'bottom center'
  });
  gsap.set([formText, closeBtn, formContainer], { 
  autoAlpha: 0
  });

if (splitTitle) {
  splitTitle.revert();
  }

splitTitle = new SplitText(formTitle, { 
  type: "words, chars",
  charsClass: "char-item" 
  });

const tl = gsap.timeline({
  defaults: { ease: 'power4.inOut' }
  });

tl.to(popupContent, { 
  scaleY: 1, 
  duration: 0.6 
  })
  .fromTo(splitTitle.chars, 
  {
  opacity: 0,
  y: 0
  },
  {
  duration: 0.3,
  opacity: 1,
  y: 0,
   /* ... */
```

### `c-design-by-dylan`

```js
document.querySelectorAll('img').forEach(img => {
  img.setAttribute('draggable', false);
});
</script><!-- Heading Big -->
<script>
document.addEventListener("DOMContentLoaded", () => {
  gsap.registerPlugin(SplitText);

document.fonts.ready.then(() => {
  // Split per woord
  const split = new SplitText(".heading-big", {
  type: "words",
  wordsClass: "word",
  });

const tl = gsap.timeline({
  defaults: { ease: "power3.out" },
  });

// 1. Fade / blur intro op de hele heading
  tl.from(".heading-big", {
  opacity: 0,
  filter: "blur(25px)",
  scale: 0.94,
  duration: 1.1,
  });

// 2. Per w /* ... */
```

### `nicola-romeitm`

```js
ocument.addEventListener("DOMContentLoaded",()=>{initButtonCharacterStagger()});
</script>

<script>
document.addEventListener("DOMContentLoaded",()=>{gsap.registerPlugin(SplitText,ScrollTrigger);let e=document.querySelectorAll('[data-split="heading"]');e.forEach(e=>{gsap.set(e,{autoAlpha:1});let l=new SplitText(e,{type:"lines",linesClass:"mask-line"});l.lines.forEach(e=>{let l=document.createElement("div");for(l.style.display="block";e.firstChild;)l.appendChild(e.firstChild);e.appendChild(l)});let t=e.querySelectorAll(".mask-line > div");gsap.from(t,{yPercent:100,duration:.85,stagger:.05,ease /* ... */
```

### `farm-minerals`

```js
ScrollTrigger.create({
  trigger: triggerElement,
  start: "top bottom",
  });
  ScrollTrigger.create({
  trigger: triggerElement,
  start: "top 90%",
  onEnter: () => timeline.play()
  });
  }

document.querySelectorAll("[text-split]").forEach(el => {
  const split = new SplitText(el, { type: "chars, words, lines" });
  const tl = gsap.timeline({ paused: true });

gsap.set(split.chars, { autoAlpha: 0 });

tl.fromTo(
  split.chars,
  { autoAlpha: 0 },
  {
  autoAlpha: 1,
  duration: 0.4,
  ease: "power2.out",
  stagger: { each: 0.02, from: "random" },
  }
  );
```

### `darknode`

```js
(element) {
  // Запобігаємо повторному запуску, якщо анімація вже відбулась
  if (element.dataset.animated === "true") return;
  element.dataset.animated = "true"; // Позначаємо елемент як "анімований"

const originalText = element.textContent;
  let splitInstance = new SplitText(element, { type: "chars" });
  const chars = splitInstance.chars;
  const originalChars = chars.map(char => char.textContent);

let animationTimeline = gsap.timeline({
  onComplete: () => {
  // Коли анімація завершена, повертаємо DOM до початкового стану
  // (видаляє
```

### `artem-shcherban-portfolio`

```js
);
  });
  }

else {
  loop = horizontalLoop(selectedItems, {
  paused: true,
  draggable: true,
  center: true,
  onChange: (element) => updateActiveElement(element)
  });

selectedMobileBlocks.forEach((target) => {
  const blockSplit = new SplitText(target, { type: "lines", mask: "lines" });
  mobileSplits.push(blockSplit);

mobileTextTimeline.fromTo(blockSplit.lines, 
  { yPercent: 100, opacity: 0 }, 
  { yPercent: 0, opacity: 1, stagger: 0, duration: 1, ease: "power2.out" }
  )
  .to(blockSplit.lines, 
  { yPercent: 100, opacity: 0,
```

## Three.js  (3 snippets from 1 sites — showing top 3)

### `darknode`

```js
deo.setAttribute("crossorigin", "anonymous");
    	this.video.muted = true;
    	this.video.loop = true;
    	this.video.playsInline = true;
    	// ---- ---------------------- ----

this.width = this.container.offsetWidth;
    	this.height = this.container.offsetHeight;
    	this.renderer = new THREE.WebGLRenderer();
    	this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    	this.renderer.setSize(this.width, this.height);
    	this.renderer.setClearColor(0xeeeeee, 1);
    	this.renderer.physicallyCorrectLights = true;
    	this.renderer.outputEncoding = THREE.sRGBEncoding;

 /* ... */
```

### `darknode`

```js
io, 2));
    	this.renderer.setSize(this.width, this.height);
    	this.renderer.setClearColor(0xeeeeee, 1);
    	this.renderer.physicallyCorrectLights = true;
    	this.renderer.outputEncoding = THREE.sRGBEncoding;

this.container.appendChild(this.renderer.domElement);

this.camera = new THREE.PerspectiveCamera(
     70,
     window.innerWidth / window.innerHeight,
     0.1,
     100
    	);

var frustumSize = 1;
    	this.camera = new THREE.OrthographicCamera(
     frustumSize / -2,
     frustumSize / 2,
     frustumSize / 2,
     frustumSize / -2,
     -1000,
     1000
    	);
    	this.cam /* ... */
```

### `darknode`

```js
set.r,0.,0.,1.);
  gl_FragColor = color;
  gl_FragColor = texture2D(uTexture,newUV - 0.01*offset.rg);
  // gl_FragColor = offset;

}`;

function clamp(number, min, max) {
    return Math.max(min, Math.min(number, max));
  }

class Sketch {
    constructor(options) {
    	this.scene = new THREE.Scene();
    	this.container = options.dom;

if (!this.container) {
     console.error("ПОМИЛКА: Контейнер #canvasContainer не знайдено!");
     return;
    	}

// Шукаємо наше ВІДЕО за ID
    	this.video = document.querySelector("#my-video-source video");

if (!this.video) {
```
