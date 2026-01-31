const syllabusInput = document.getElementById("syllabusFile");
const notesInput = document.getElementById("notesFile");

syllabusInput.addEventListener("change", () => {
  showPreview(syllabusInput, "syllabusPreview", "/upload/syllabus");
});

notesInput.addEventListener("change", () => {
  showPreview(notesInput, "notesPreview", "/upload/notes");
});

function showPreview(input, previewId, url) {
  const file = input.files[0];
  if (!file) return;

  document.getElementById(previewId).innerHTML = `
    ✅ <strong>${file.name}</strong><br>
    <small>${(file.size / 1024).toFixed(2)} KB</small>
  `;

  const formData = new FormData();
  formData.append("file", file);

  fetch(url, {
    method: "POST",
    body: formData
  });
}
