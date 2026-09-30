export function formatRepoName(fullName: string): string {
  const slug = fullName.split("/").pop() || fullName;
  return slug
    .replace(/[-_]+/g, " ")
    .split(" ")
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}
