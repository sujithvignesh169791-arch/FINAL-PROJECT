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

  // Fix Sidebar flex hidden
  content = content.replace(/flex flex-col hidden md:flex/g, 'hidden md:flex flex-col');
  content = content.replace(/flex flex-col hidden/g, 'hidden flex-col');
  content = content.replace(/hidden md:flex flex-col flex/g, 'hidden md:flex flex-col');

  // Fix inputs in all files
  // Remove text-ivory from inputs because it conflicts with placeholders
  content = content.replace(/text-ivory (placeholder:text-white\/30|placeholder-white\/30)/g, '$1');
  content = content.replace(/(placeholder:text-white\/30|placeholder-white\/30) text-ivory/g, '$1');
  
  // Remove focus:border-gold/50
  content = content.replace(/ focus:border-gold\/50/g, '');
  content = content.replace(/focus:border-gold\/50 /g, '');
  
  // Remove focus-within:border-gold/50
  content = content.replace(/ focus-within:border-gold\/50/g, ' focus-within:ring-1 focus-within:ring-gold/50');
  content = content.replace(/focus-within:border-gold\/50 /g, 'focus-within:ring-1 focus-within:ring-gold/50 ');

  // Fix Comparison page
  content = content.replace(/text-white\/80 leading-relaxed mb-4 bg-green-900\/20 text-green-100/g, 'leading-relaxed mb-4 bg-green-900/20 text-green-100');
  
  // Also fix placeholder:text-white/30 in general
  content = content.replace(/text-ivory placeholder:text-white\/30/g, 'placeholder:text-white/30');

  // Just to be extremely safe, remove text-ivory anywhere it's next to a placeholder
  content = content.replace(/text-ivory (?=placeholder)/g, '');
  
  if (content !== original) {
    fs.writeFileSync(file, content, 'utf8');
    console.log('SuperFixed', file);
  }
}
