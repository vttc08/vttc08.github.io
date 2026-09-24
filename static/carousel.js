class XCarousel extends HTMLElement {
    constructor() {
        super();
        this.activeIndex = 0;
        // CSS without affecting the rest of the page
        this.attachShadow({ mode: "open" });

        this.shadowRoot.innerHTML = `
        <style>
            :host {
                display: block;
                width: 100%;
            }

            .carousel {
                position: relative;
                width: 100%;
                aspect-ratio: var(--carousel-aspect-ratio, 16 / 9);
                overflow: hidden;
            }

            .viewport {
                display: flex;
                flex-direction: row;
                width: 100%;
                height: 100%;

                overflow-x: auto;
                overflow-y: hidden;

                scroll-snap-type: x mandatory;
                scroll-behavior: smooth;

                /* Hide scrollbar */
                scrollbar-width: none;

                /* Better touch behavior */
                touch-action: pan-x;
                overscroll-behavior-x: contain;
            }

            .viewport::-webkit-scrollbar {
                display: none;
            }

            ::slotted(img) {
                flex: 0 0 100%;
                width: 100%;
                height: 100%;

                object-fit: cover;

                scroll-snap-align: start;
                scroll-snap-stop: always;
            }

            button {
                position: absolute;
                top: 50%;
                transform: translateY(-50%);

                z-index: 10;

                width: 25px;
                height: 100%;

                background: rgba(0, 0, 0, 0.3);
                color: white;
                border: none;

                font-size: 24px;
                cursor: pointer;
                transition: background-color 180ms ease;
            }

            @media (max-width: 760px) {
                button {
                    width: 30px;
                }
            }

            @media (hover: hover) {
                button {
                    opacity: 0;
                    pointer-events: none;
                    transition: opacity 180ms ease, transform 180ms ease,
                        background-color 180ms ease;
                }

                .prev {
                    transform: translate(-8px, -50%);
                }

                .next {
                    transform: translate(8px, -50%);
                }

                .carousel:is(:hover, :focus-within) button {
                    opacity: 1;
                    pointer-events: auto;
                    transform: translate(0, -50%);
                }
            }

            @media (prefers-reduced-motion: reduce) {
                button {
                    transition: none;
                }
            }

            .prev {
                left: 0px;
            }

            .next {
                right: 0px;
            }

            button:hover {
                background: rgba(0, 0, 0, 0.7);
            }

            .indicators {
                position: absolute;
                bottom: 8px;
                display: flex;
                gap: 4px;
                z-index: 10;
                width: 100%;
                justify-content: center;
            }
        </style>

        <div class="carousel">
            <div class="viewport">
            <slot></slot>
            </div>
            <div class="indicators"></div>
            <button class="prev" aria-label="Previous image">‹</button>
            <button class="next" aria-label="Next image">›</button>
        </div>
        `;
    }



    connectedCallback() {
        this.viewport = this.shadowRoot.querySelector(".viewport");

        this.shadowRoot
        .querySelector(".prev")
        .addEventListener("click", () => {
            this.previous();
        });

        this.shadowRoot
        .querySelector(".next")
        .addEventListener("click", () => {
            this.next();
        });

        this.updateIndicators();

        this.viewport.addEventListener("scrollend", () => {
            this.activeIndex = this.currentIndex;
            this.updateIndicators();
        });

    }

    get currentIndex() {
        return Math.round(
        this.viewport.scrollLeft / this.viewport.clientWidth
        );
    }

    get childrenCount() {
        const slot = this.shadowRoot.querySelector("slot");
        return slot.assignedElements().length;
    }

    goTo(index) {
        if (this.childrenCount === 0) return;

        this.activeIndex = (index + this.childrenCount) % this.childrenCount;
        this.viewport.scrollTo({
            left: this.activeIndex * this.viewport.clientWidth,
            behavior: "smooth"
        });
        this.updateIndicators();
    }

    updateIndicators() {
        const indicatorsContainer = this.shadowRoot.querySelector(".indicators");
        indicatorsContainer.innerHTML = "";

        for (let i = 0; i < this.childrenCount; i++) {
        const indicator = document.createElement("span");
        indicator.style.width = "8px";
        indicator.style.height = "8px";
        indicator.style.borderRadius = "50%";
        indicator.style.backgroundColor =
            i === this.activeIndex ? "white" : "rgba(255, 255, 255, 0.5)";
        indicatorsContainer.appendChild(indicator);
        }

        this.dispatchEvent(new CustomEvent("carouselchange", {
            bubbles: true,
            composed: true,
            detail: {
                index: this.activeIndex,
                total: this.childrenCount,
            },
        }));
    }


    next() {
        this.goTo(this.activeIndex + 1);
    }

    previous() {
        this.goTo(this.activeIndex - 1);
    }
    }

if (!customElements.get("x-carousel")) {
    customElements.define("x-carousel", XCarousel);
}
