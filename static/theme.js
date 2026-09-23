const themeButton = document.querySelector("#theme-icon");
const root = document.documentElement;

const savedTheme = localStorage.getItem("theme");

if (savedTheme) {
  root.dataset.theme = savedTheme;
}

themeButton.addEventListener("click", () => {
  const isDark =
    root.dataset.theme === "dark" ||
    (!root.dataset.theme &&
      window.matchMedia("(prefers-color-scheme: dark)").matches);

  const newTheme = isDark ? "light" : "dark";

  root.dataset.theme = newTheme;
  localStorage.setItem("theme", newTheme);
});