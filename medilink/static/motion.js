/* motion.js - a few small, optional animations built on GSAP (static/vendor/gsap/gsap.min.js).
 *
 * Rules:
 *  - Everything works without this file and without JavaScript: it only adds movement.
 *  - Off when the visitor asked for reduced motion (prefers-reduced-motion) or when GSAP did not load.
 *  - Safety information (emergency numbers, notices, warnings) is never hidden or animated.
 */
(function () {
    var reduced = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
    var on = !!window.gsap && !reduced;
    var rtl = document.documentElement.getAttribute('dir') === 'rtl';
    var M = { enabled: on };

    // a small "pop" when something is ticked
    M.pop = function (el) {
        if (!on || !el) { return; }
        gsap.fromTo(el, { scale: 0.97 }, { scale: 1, duration: 0.35, ease: 'back.out(3)', clearProps: 'transform' });
    };

    // a bar that fills from where reading starts (left, or right in Arabic)
    M.fill = function (el) {
        if (!on || !el) { return; }
        gsap.fromTo(el, { scaleX: 0, transformOrigin: rtl ? 'right center' : 'left center' },
                    { scaleX: 1, duration: 0.7, ease: 'power2.out', clearProps: 'transform,transformOrigin' });
    };

    // result badge and list items appear one after another (they are visible without JS and stay in the page flow)
    M.reveal = function (nodes) {
        if (!on || !nodes || !nodes.length) { return; }
        gsap.from(nodes, { opacity: 0, y: 12, duration: 0.45, stagger: 0.12, ease: 'power2.out', clearProps: 'opacity,transform' });
    };

    // short message: returns true when it handled the movement (otherwise the caller uses plain CSS)
    M.toast = function (el, visible) {
        if (!on || !el) { return false; }
        gsap.killTweensOf(el);
        if (visible) { gsap.fromTo(el, { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.25, ease: 'power2.out' }); }
        else { gsap.to(el, { opacity: 0, y: 10, duration: 0.2, ease: 'power2.in' }); }
        return true;
    };

    // <details class="sc-sec"> opens and closes smoothly; without GSAP the browser does its normal instant toggle
    M.collapsibles = function (root) {
        if (!on || !root) { return; }
        root.querySelectorAll('details.sc-sec > summary').forEach(function (summary) {
            summary.addEventListener('click', function (e) {
                var d = summary.parentNode, body = d.querySelector('.sc-body');
                if (!body) { return; }
                e.preventDefault();
                gsap.killTweensOf(body);
                var clear = { clearProps: 'height,opacity,overflow' };
                if (d.dataset.closing === '1') { delete d.dataset.closing; gsap.set(body, clear); return; }   // clicked again while closing: stay open
                if (d.open) {
                    d.dataset.closing = '1';
                    gsap.to(body, { height: 0, opacity: 0, overflow: 'hidden', duration: 0.25, ease: 'power2.in',
                                    onComplete: function () { d.open = false; delete d.dataset.closing; gsap.set(body, clear); } });
                } else {
                    d.open = true;
                    gsap.from(body, { height: 0, opacity: 0, overflow: 'hidden', duration: 0.3, ease: 'power2.out', clearProps: 'height,opacity,overflow' });
                }
            });
        });
    };

    window.FahemniMotion = M;
})();
