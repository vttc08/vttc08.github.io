const allowedFilters = new Set([
  "all", "featured", "homelab", "development", "media",
]);

// homepage defaults to featured, posts page defaults to all
const initialFilter = window.location.pathname.includes("/posts") ? "all" : "featured";

// search filter from URL query parameter
function readFilter() {
  const value = new URL(location.href).searchParams.get("category");
  return allowedFilters.has(value) ? value : initialFilter;
}


function applyFilter(filter) {
  // Hide non matching cards
  document.querySelectorAll("[data-project-card]").forEach(card => {
    const matches =
      filter === "all" ||
      (filter === "featured" && card.dataset.featured === "true") ||
      card.dataset.category === filter;

    card.hidden = !matches;
  });

  // Update button states
  document.querySelectorAll("[data-filter-value]").forEach(button => {
    button.setAttribute(
      "aria-pressed",
      String(button.dataset.filterValue === filter),
    );
  });
}

document.querySelectorAll("[data-filter-value]").forEach(button => {
  button.addEventListener("click", () => {
    const filter = button.dataset.filterValue;
    const url = new URL(location.href);
    if (filter !== "featured") {
        // Homepage: do not append query parameter for featured filter, to keep the URL clean
        url.searchParams.set("category", filter);
        history.pushState({ category: filter }, "", url);
    } else {
        url.searchParams.delete("category");
        history.pushState({ category: filter }, "", url);
    }
    applyFilter(filter);
  });
});

window.addEventListener("popstate", () => applyFilter(readFilter())); // Handle back/forward navigation

applyFilter(readFilter());