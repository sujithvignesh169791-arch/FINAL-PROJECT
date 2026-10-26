const fs = require('fs');
const path = require('path');

function getFiles(dir, filesList = []) {
  const files = fs.readdirSync(dir);
  for (const file of files) {
    const name = dir + '/' + file;
    if (fs.statSync(name).isDirectory()) {
      getFiles(name, filesList);
    } else if (name.endsWith('.tsx')) {
      filesList.push(name);
    }
  }
  return filesList;
}

const files = getFiles('src');

for (const file of files) {
  let content = fs.readFileSync(file, 'utf8');
  let original = content;

  // 1. Sidebar.tsx
  content = content.replace(/flex flex-col hidden/g, 'hidden flex-col');

  // 2. Settings gradients
  content = content.replace(/bg-gradient-to-/g, 'bg-linear-to-');

  // 3. Comparison text color collision
  content = content.replace(/text-white\/80 leading-relaxed mb-4 bg-green-900\/20 text-green-100/g, 'leading-relaxed mb-4 bg-green-900/20 text-green-100');

  // 4. placeholder text color
  content = content.replace(/placeholder:text-white\/30/g, 'placeholder-white/30');

  // 5. focus border color conflicts
  content = content.replace(/ focus:border-gold\/50/g, '');
  content = content.replace(/ focus-within:border-gold\/50/g, ' focus-within:ring-1 focus-within:ring-gold/50');

  if (content !== original) {
    fs.writeFileSync(file, content, 'utf8');
    console.log('Fixed', file);
  }
}
