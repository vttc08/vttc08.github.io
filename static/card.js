class ProjectCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this.abortController = null;

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          color: var(--text, #2a2a2a);
          font-family: var(--font-body, "Roboto", sans-serif);
        }

        article {
          display: grid;
          grid-template-columns: minmax(13rem, 0.64fr) minmax(0, 1.36fr);
          overflow: hidden;
          border-radius: var(--card-border-radius, 0.375rem);
          background: var(--card-background);
        }

        .media {
          min-width: 0;
        }

        ::slotted(x-carousel[slot="media"]) {
          display: block;
          width: 100%;
          --carousel-aspect-ratio: 4/3;
        }

        .copy {
          display: flex;
          min-width: 0;
          flex-direction: column;
          padding: 1rem;
        }

        .meta {
          display: flex;
          flex-wrap: wrap;
          justify-content: space-between;
          gap: 0.2rem 1rem;
          margin-bottom: 0.25rem;
          color: var(--text-light, #59616d);
          font-family: var(--font-mono, "Geist Mono", monospace);
          font-size: 0.85rem;
          line-height: 1.5;
          letter-spacing: 0.025em;
          text-transform: uppercase;
        }

        ::slotted([slot="title"]) {
          margin: 0 !important;
          color: var(--text, #2a2a2a) !important;
          font-family: var(--font-display, "REM", sans-serif) !important;
          font-size: clamp(1.1rem, 3vw, 1.25rem) !important;
          font-weight: 600 !important;
          line-height: normal !important;
          letter-spacing: -0.025em !important;
          overflow-wrap: anywhere;
        }

        .description {
          margin: 0.25rem 0;
          color: var(--text-light, #59616d);
        }

        ::slotted([slot="description"]) {
          margin: 0 !important;
          color: inherit;
          font: inherit !important;
        }

        .tags {
          display: flex;
          flex-wrap: wrap;
          gap: 0.4rem;
        }

        ::slotted([slot="tag"]) {
          display: inline-flex;
          padding: 0.15rem 0.5rem;
          border: 1px solid var(--border, #8c909d);
          border-radius: 999px;
          color: var(--text-light, #59616d);
          font-family: var(--font-mono, "Geist Mono", monospace);
          font-size: 0.72rem;
          line-height: 1.4;
          white-space: nowrap;
        }

        footer {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 1rem;
          margin-top: auto;
        }

        ::slotted(a[slot="link"]) {
          color: var(--accent, #3974ce);
          font-family: var(--font-mono, "Geist Mono", monospace);
          font-size: 0.9rem;
          font-weight: 600;
          line-height: 1.3;
          text-decoration-thickness: 1px;
          text-underline-offset: 0.2em;
        }

        ::slotted(a[slot="link"]:hover),
        ::slotted(a[slot="link"]:focus-visible) {
          color: var(--accent-hover, #235cb1);
        }

        .slide-count {
          flex-shrink: 0;
          color: var(--text-light, #59616d);
          font-family: var(--font-mono, "Geist Mono", monospace);
          font-size: 0.72rem;
          line-height: 1;
        }

        @media (min-width: 761px) and (max-width: 1024px) {
          ::slotted(x-carousel[slot="media"]) {
            --carousel-aspect-ratio: 1/1;
          }
        }

        @media (max-width: 760px) {
          article {
            grid-template-columns: 1fr;
          }

          .media {
            border-inline-end: 0;
          }

          ::slotted(x-carousel[slot="media"]) {
            --carousel-aspect-ratio: 16 / 9;
          }

          footer {
            align-items: flex-start;
            flex-direction: column;
          }
        }
        @media (min-width: 560px) and (max-width: 760px) {
          ::slotted(x-carousel[slot="media"]) {
            --carousel-aspect-ratio: 2/1;
          }
        }
      </style>

      <article>
        <div class="media">
          <slot name="media"></slot>
        </div>

        <div class="copy">
          <div class="meta">
            <slot name="date"></slot>
            <slot name="category"></slot>
          </div>

          <slot name="title"></slot>

          <div class="description">
            <slot name="description"></slot>
          </div>

          <div class="tags" part="tags">
            <slot name="tag"></slot>
          </div>

          <footer>
            <slot name="link"></slot>
            <span class="slide-count" aria-live="polite">1 / 1</span>
          </footer>
        </div>
      </article>
    `;
  }

  connectedCallback() {
    this.abortController?.abort();
    this.abortController = new AbortController();

    this.addEventListener(
      "carouselchange",
      (event) => this.updateSlideCount(event.detail.index, event.detail.total),
      { signal: this.abortController.signal },
    );

    const mediaSlot = this.shadowRoot.querySelector('slot[name="media"]');
    mediaSlot.addEventListener(
      "slotchange",
      () => this.updateInitialSlideCount(),
      { signal: this.abortController.signal },
    );

    this.updateInitialSlideCount();
  }

  disconnectedCallback() {
    this.abortController?.abort();
  }

  updateInitialSlideCount() {
    const carousel = this.querySelector('x-carousel[slot="media"]');
    const total = carousel?.children.length ?? 0;
    this.updateSlideCount(total > 0 ? 0 : -1, total);
  }

  updateSlideCount(index, total) {
    const counter = this.shadowRoot.querySelector(".slide-count");
    counter.hidden = total < 2;
    counter.textContent = total > 0 ? `${index + 1} / ${total}` : "";
  }
}

if (!customElements.get("x-card")) {
  customElements.define("x-card", ProjectCard);
}
