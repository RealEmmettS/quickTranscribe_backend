// transcribe.js
document.getElementById('submit').addEventListener('click', uploadFile);

function uploadFile() {
  const fileInput = document.getElementById('file_input');
  const file = fileInput.files[0];

  if (!file) {
    alert('Please select a file');
    return;
  }

  const formData = new FormData();
  formData.append('file', file);

  fetch('https://aitranscribe.replit.app/transcribe', {
    method: 'POST',
    body: formData
  })
    .then(response => response.blob())
    .then(blob => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'transcription.txt';
      document.body.appendChild(a);
      a.click();
      a.remove();
    })
    .catch(error => {
      console.error('Error:', error);
      alert('An error occurred while processing the file');
    });
}