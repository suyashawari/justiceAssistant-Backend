// const fs = require('fs').promises;
// const path = require('path');

// const OUTPUT_FILE = 'code.txt';
// const SPACER = '\n\n\n\n\n';

// // Binary file extensions
// const EXCLUDED_EXTENSIONS = new Set([
//   '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg',
//   '.mp4', '.mp3', '.wav', '.avi', '.mov', '.webm',
//   '.apk', '.zip', '.jar', '.dex', '.ttf', '.ico', '.webp',
//   '.data', '.index', '.prof', '.tfevents', '.bin', '.so',
//   '.exe', '.dll', '.o', '.a', '.dylib', '.class', '.pyc',
//   '.pyo', '.pyd', '.so', '.whl', '.egg',
// ]);

// // Excluded directories
// // const EXCLUDED_DIRECTORIES = new Set([
// //   'node_modules',
// //   'venv',
// //   'env',
// //   '.venv',
// //   '__pycache__',
// //   '.git',
// //   '.pytest_cache',
// //   'dist',
// //   'build',
// //   '.egg-info',
// //   '.tox',
// //   'site-packages',
// //   '.next',
// //   'out',
// //   'coverage',
// //   '.nyc_output',
// //   '.cache',
// //   '.idea',
// //   '.vscode',
// // ]);
// const EXCLUDED_DIRECTORIES = new Set([
//   'node_modules',
//   'venv',
//   'env',
//   '.venv',
//   '__pycache__',
//   '.git',
//   '.pytest_cache',
//   'dist',
//   'build',
//   '.egg-info',
//   '.tox',
//   'site-packages',
//   '.next',
//   'out',
//   'coverage',
//   '.nyc_output',
//   '.cache',
//   '.idea',
//   '.vscode',
//   'instance',
//   'migrations',
//   'uploads',
//   '.geojson '
// ]);
// // Excluded file names
// const EXCLUDED_FILE_NAMES = new Set([
//   OUTPUT_FILE,
//   'package-lock.json',
//   'yarn.lock',
//   'poetry.lock',
//   'Pipfile.lock',
//   '.DS_Store',
//   'thumbs.db',
//   '.gitignore',
//   '.gitkeep',
// ]);

// // Excluded patterns (regex)
// const EXCLUDED_PATTERNS = [
//   /^\./, // Hidden files
//   /\.log$/, // Log files
//   /\.tmp$/, // Temp files
//   /\.cache$/, // Cache files
// ];

// function isReactProject() {
//   try {
//     const packageJson = require('./package.json');
//     return packageJson.dependencies && 
//            (packageJson.dependencies.react || packageJson.devDependencies?.react);
//   } catch {
//     return false;
//   }
// }

// function isPythonProject() {
//   try {
//     const files = require('fs').readdirSync('.');
//     return files.includes('requirements.txt') || 
//            files.includes('setup.py') || 
//            files.includes('pyproject.toml') ||
//            files.includes('Pipfile');
//   } catch {
//     return false;
//   }
// }

// function shouldExcludeFile(fileName) {
//   // Check exact file names
//   if (EXCLUDED_FILE_NAMES.has(fileName)) return true;

//   // Check extensions
//   const ext = path.extname(fileName).toLowerCase();
//   if (EXCLUDED_EXTENSIONS.has(ext)) return true;

//   // Check patterns
//   if (EXCLUDED_PATTERNS.some(pattern => pattern.test(fileName))) return true;

//   return false;
// }

// function shouldExcludeDirectory(dirName) {
//   return EXCLUDED_DIRECTORIES.has(dirName);
// }

// async function isBinary(filePath) {
//   try {
//     const stat = await fs.stat(filePath);
//     if (!stat.isFile()) return true;

//     const buffer = await fs.readFile(filePath);
//     const textChars = buffer.slice(0, 512).toString('utf8');
//     return /\u0000/.test(textChars) || buffer.includes(0x00);
//   } catch (err) {
//     return true;
//   }
// }

// async function collectReadableFiles(dirPath, baseDir = null) {
//   if (baseDir === null) baseDir = dirPath;
  
//   const files = [];

//   try {
//     const entries = await fs.readdir(dirPath, { withFileTypes: true });

//     for (const entry of entries) {
//       const fullPath = path.join(dirPath, entry.name);

//       if (entry.isDirectory()) {
//         // Skip excluded directories
//         if (!shouldExcludeDirectory(entry.name)) {
//           console.log(`📁 Scanning directory: ${path.relative(baseDir, fullPath)}/`);
//           const subFiles = await collectReadableFiles(fullPath, baseDir);
//           files.push(...subFiles);
//         } else {
//           console.log(`⏭️  Skipping directory: ${path.relative(baseDir, fullPath)}/`);
//         }
//       } else if (
//         !shouldExcludeFile(entry.name) &&
//         !(await isBinary(fullPath))
//       ) {
//         files.push(fullPath);
//       }
//     }
//   } catch (err) {
//     console.error(`Error reading directory ${dirPath}: ${err.message}`);
//   }

//   return files;
// }

// async function buildDirectoryTree(dirPath, prefix = '', baseDir = null) {
//   if (baseDir === null) baseDir = dirPath;
  
//   const lines = [];
  
//   try {
//     const entries = await fs.readdir(dirPath, { withFileTypes: true });
//     entries.sort((a, b) => a.name.localeCompare(b.name));

//     for (let i = 0; i < entries.length; i++) {
//       const entry = entries[i];
//       const isLast = i === entries.length - 1;
//       const connector = isLast ? '└── ' : '├── ';
//       const extension = isLast ? '    ' : '│   ';

//       if (entry.isDirectory()) {
//         if (!shouldExcludeDirectory(entry.name)) {
//           lines.push(`${prefix}${connector}${entry.name}/`);
//           const subLines = await buildDirectoryTree(
//             path.join(dirPath, entry.name),
//             prefix + extension,
//             baseDir
//           );
//           lines.push(...subLines);
//         }
//       } else {
//         if (!shouldExcludeFile(entry.name)) {
//           lines.push(`${prefix}${connector}${entry.name}`);
//         }
//       }
//     }
//   } catch (err) {
//     console.error(`Error building tree for ${dirPath}: ${err.message}`);
//   }

//   return lines;
// }

// async function combineFiles() {
//   console.log('🚀 Combining readable code files from current directory...\n');
  
//   const cwd = process.cwd();
//   const isReact = isReactProject();
//   const isPython = isPythonProject();
  
//   if (isReact) {
//     console.log('📦 Detected React project\n');
//   }
//   if (isPython) {
//     console.log('🐍 Detected Python/Flask project\n');
//   }
//   if (!isReact && !isPython) {
//     console.log('📁 No specific project type detected\n');
//   }

//   try {
//     console.log('Building directory tree...\n');
//     const treeLines = await buildDirectoryTree(cwd);
//     const treeContent = path.basename(cwd) + '/\n' + treeLines.join('\n');
//     await fs.writeFile(OUTPUT_FILE, treeContent + SPACER);

//     console.log('Collecting files...\n');
//     const files = await collectReadableFiles(cwd);

//     if (files.length === 0) {
//       console.log('⚠️  No readable files found to combine');
//       return;
//     }

//     console.log(`\n📂 Found ${files.length} files to combine\n`);

//     for (const filePath of files) {
//       try {
//         const relativePath = path.relative(cwd, filePath);
//         console.log(`  ✓ Including: ${relativePath}`);
//         const content = await fs.readFile(filePath, 'utf8');
//         const header = `==================== ${relativePath} ====================\n\n`;
//         await fs.appendFile(OUTPUT_FILE, header + content + SPACER);
//       } catch (err) {
//         const error = `!!!!!!!!!!!! ERROR reading ${filePath} !!!!!!!!!!!!\n${SPACER}`;
//         await fs.appendFile(OUTPUT_FILE, error);
//         console.error(`  ✗ Skipped ${filePath}: ${err.message}`);
//       }
//     }

//     console.log(`\n✅ Done! Output saved to ${OUTPUT_FILE}`);
//     console.log(`📊 Total files combined: ${files.length}`);
//   } catch (err) {
//     console.error(`\n🔥 Fatal error: ${err.message}`);
//   }
// }

// combineFiles();


const fs = require('fs').promises;
const path = require('path');

const OUTPUT_FILE = 'code.txt';
const SPACER = '\n\n\n\n\n';

// Binary file extensions
const EXCLUDED_EXTENSIONS = new Set([
  '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg',
  '.mp4', '.mp3', '.wav', '.avi', '.mov', '.webm',
  '.apk', '.zip', '.jar', '.dex', '.ttf', '.ico', '.webp',
  '.data', '.index', '.prof', '.tfevents', '.bin', '.so',
  '.exe', '.dll', '.o', '.a', '.dylib', '.class', '.pyc',
  '.pyo', '.pyd', '.whl', '.egg','.json','.geojson'
]);

// Excluded directories
const EXCLUDED_DIRECTORIES = new Set([
  'node_modules',
  'venv',
  'env',
  '.venv',
  '__pycache__',
  '.git',
  '.pytest_cache',
  'dist',
  'build',
  '.egg-info',
  '.tox',
  'site-packages',
  '.next',
  'out',
  'coverage',
  '.nyc_output',
  '.cache',
  '.idea',
  '.vscode',
  'instance',
  'migrations',
  'uploads',
  '.geojson',
  'target',
  'bin',
  'obj',
  '.gradle',
  '.mvn',
  '.json'
]);

// Excluded file names
const EXCLUDED_FILE_NAMES = new Set([
  OUTPUT_FILE,
  'package-lock.json',
  'yarn.lock',
  'poetry.lock',
  'Pipfile.lock',
  'india.geojson',
  '.DS_Store',
  'thumbs.db',
  '.gitignore',
  '.gitkeep',
]);

// Excluded patterns (regex)
const EXCLUDED_PATTERNS = [
  /^\./, // Hidden files
  /\.log$/, // Log files
  /\.tmp$/, // Temp files
  /\.cache$/, // Cache files
];

// File extensions that support comments
const COMMENT_SUPPORT = {
  // C-style comments (// and /* */)
  cStyle: ['.js', '.jsx', '.ts', '.tsx', '.java', '.c', '.cpp', '.cc', '.h', '.hpp', '.cs', '.go', '.rs', '.swift', '.kt', '.scala', '.php'],
  // Python-style comments (#)
  python: ['.py', '.rb', '.sh', '.bash', '.yaml', '.yml', '.r', '.pl', '.conf'],
  // HTML/XML comments (<!-- -->)
  html: ['.html', '.htm', '.xml', '.svg'],
  // CSS comments (/* */)
  css: ['.css', '.scss', '.sass', '.less'],
  // SQL comments (-- and /* */)
  sql: ['.sql'],
};

function getFileType(fileName) {
  const ext = path.extname(fileName).toLowerCase();
  
  if (COMMENT_SUPPORT.cStyle.includes(ext)) return 'cStyle';
  if (COMMENT_SUPPORT.python.includes(ext)) return 'python';
  if (COMMENT_SUPPORT.html.includes(ext)) return 'html';
  if (COMMENT_SUPPORT.css.includes(ext)) return 'css';
  if (COMMENT_SUPPORT.sql.includes(ext)) return 'sql';
  
  return null;
}

function removeComments(content, fileType) {
  if (!fileType) return content;

  let result = content;

  switch (fileType) {
    case 'cStyle':
      result = removeCStyleComments(result);
      break;
    case 'python':
      result = removePythonComments(result);
      break;
    case 'html':
      result = removeHtmlComments(result);
      break;
    case 'css':
      result = removeCssComments(result);
      break;
    case 'sql':
      result = removeSqlComments(result);
      break;
  }

  // Remove excessive blank lines (more than 2 consecutive)
  result = result.replace(/\n\s*\n\s*\n+/g, '\n\n');
  
  // Trim trailing whitespace from each line
  result = result.split('\n').map(line => line.trimEnd()).join('\n');

  return result;
}

function removeCStyleComments(content) {
  let result = '';
  let i = 0;
  let inString = false;
  let stringChar = '';
  let inSingleLineComment = false;
  let inMultiLineComment = false;

  while (i < content.length) {
    const char = content[i];
    const nextChar = content[i + 1];

    // Handle strings
    if (!inSingleLineComment && !inMultiLineComment) {
      if ((char === '"' || char === "'" || char === '`') && (i === 0 || content[i - 1] !== '\\')) {
        if (!inString) {
          inString = true;
          stringChar = char;
          result += char;
          i++;
          continue;
        } else if (char === stringChar) {
          inString = false;
          stringChar = '';
          result += char;
          i++;
          continue;
        }
      }
    }

    // If in string, just add character
    if (inString) {
      result += char;
      i++;
      continue;
    }

    // Handle single-line comments - DON'T preserve the newline
    if (!inMultiLineComment && char === '/' && nextChar === '/') {
      inSingleLineComment = true;
      i += 2;
      continue;
    }

    if (inSingleLineComment) {
      if (char === '\n') {
        inSingleLineComment = false;
        // DON'T add the newline - just skip it
      }
      i++;
      continue;
    }

    // Handle multi-line comments
    if (!inSingleLineComment && char === '/' && nextChar === '*') {
      inMultiLineComment = true;
      i += 2;
      continue;
    }

    if (inMultiLineComment) {
      if (char === '*' && nextChar === '/') {
        inMultiLineComment = false;
        i += 2;
        continue;
      }
      i++;
      continue;
    }

    // Normal character
    result += char;
    i++;
  }

  return result;
}

function removePythonComments(content) {
  const lines = content.split('\n');
  const result = [];
  let inMultiLineString = false;
  let multiLineChar = '';

  for (let line of lines) {
    let processedLine = '';
    let i = 0;
    let inString = false;
    let stringChar = '';

    while (i < line.length) {
      const char = line[i];
      const next2 = line.substring(i, i + 3);

      // Handle triple-quoted strings (docstrings) - REMOVE them, don't preserve
      if (!inString && (next2 === '"""' || next2 === "'''")) {
        if (!inMultiLineString) {
          inMultiLineString = true;
          multiLineChar = next2;
          i += 3;
          continue;
        } else if (next2 === multiLineChar) {
          inMultiLineString = false;
          multiLineChar = '';
          i += 3;
          continue;
        }
      }

      if (inMultiLineString) {
        i++;
        continue;
      }

      // Handle regular strings
      if ((char === '"' || char === "'") && (i === 0 || line[i - 1] !== '\\')) {
        if (!inString) {
          inString = true;
          stringChar = char;
        } else if (char === stringChar) {
          inString = false;
          stringChar = '';
        }
        processedLine += char;
        i++;
        continue;
      }

      // Handle comments - everything after # is removed
      if (!inString && char === '#') {
        break;
      }

      processedLine += char;
      i++;
    }

    // Only add non-empty lines (no blank line preservation)
    if (!inMultiLineString) {
      const trimmed = processedLine.trim();
      if (trimmed.length > 0) {
        result.push(processedLine.trimEnd());
      }
    }
  }

  return result.join('\n');
}

function removeHtmlComments(content) {
  return content.replace(/<!--[\s\S]*?-->/g, '');
}

function removeCssComments(content) {
  return content.replace(/\/\*[\s\S]*?\*\//g, '');
}

function removeSqlComments(content) {
  let result = content;
  
  // Remove multi-line comments
  result = result.replace(/\/\*[\s\S]*?\*\//g, '');
  
  // Remove single-line comments and empty lines
  const lines = result.split('\n');
  const processedLines = lines
    .map(line => {
      const commentIndex = line.indexOf('--');
      if (commentIndex !== -1) {
        return line.substring(0, commentIndex).trimEnd();
      }
      return line.trimEnd();
    })
    .filter(line => line.length > 0); // Remove empty lines
  
  return processedLines.join('\n');
}

function isReactProject() {
  try {
    const packageJson = require('./package.json');
    return packageJson.dependencies && 
           (packageJson.dependencies.react || packageJson.devDependencies?.react);
  } catch {
    return false;
  }
}

function isPythonProject() {
  try {
    const files = require('fs').readdirSync('.');
    return files.includes('requirements.txt') || 
           files.includes('setup.py') || 
           files.includes('pyproject.toml') ||
           files.includes('Pipfile');
  } catch {
    return false;
  }
}

function shouldExcludeFile(fileName) {
  if (EXCLUDED_FILE_NAMES.has(fileName)) return true;
  const ext = path.extname(fileName).toLowerCase();
  if (EXCLUDED_EXTENSIONS.has(ext)) return true;
  if (EXCLUDED_PATTERNS.some(pattern => pattern.test(fileName))) return true;
  return false;
}

function shouldExcludeDirectory(dirName) {
  return EXCLUDED_DIRECTORIES.has(dirName);
}

async function isBinary(filePath) {
  try {
    const stat = await fs.stat(filePath);
    if (!stat.isFile()) return true;

    const buffer = await fs.readFile(filePath);
    const textChars = buffer.slice(0, 512).toString('utf8');
    return /\u0000/.test(textChars) || buffer.includes(0x00);
  } catch (err) {
    return true;
  }
}

async function collectReadableFiles(dirPath, baseDir = null) {
  if (baseDir === null) baseDir = dirPath;
  
  const files = [];

  try {
    const entries = await fs.readdir(dirPath, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dirPath, entry.name);

      if (entry.isDirectory()) {
        if (!shouldExcludeDirectory(entry.name)) {
          console.log(`📁 Scanning directory: ${path.relative(baseDir, fullPath)}/`);
          const subFiles = await collectReadableFiles(fullPath, baseDir);
          files.push(...subFiles);
        } else {
          console.log(`⏭️  Skipping directory: ${path.relative(baseDir, fullPath)}/`);
        }
      } else if (
        !shouldExcludeFile(entry.name) &&
        !(await isBinary(fullPath))
      ) {
        files.push(fullPath);
      }
    }
  } catch (err) {
    console.error(`Error reading directory ${dirPath}: ${err.message}`);
  }

  return files;
}

async function buildDirectoryTree(dirPath, prefix = '', baseDir = null) {
  if (baseDir === null) baseDir = dirPath;
  
  const lines = [];
  
  try {
    const entries = await fs.readdir(dirPath, { withFileTypes: true });
    entries.sort((a, b) => a.name.localeCompare(b.name));

    for (let i = 0; i < entries.length; i++) {
      const entry = entries[i];
      const isLast = i === entries.length - 1;
      const connector = isLast ? '└── ' : '├── ';
      const extension = isLast ? '    ' : '│   ';

      if (entry.isDirectory()) {
        if (!shouldExcludeDirectory(entry.name)) {
          lines.push(`${prefix}${connector}${entry.name}/`);
          const subLines = await buildDirectoryTree(
            path.join(dirPath, entry.name),
            prefix + extension,
            baseDir
          );
          lines.push(...subLines);
        }
      } else {
        if (!shouldExcludeFile(entry.name)) {
          lines.push(`${prefix}${connector}${entry.name}`);
        }
      }
    }
  } catch (err) {
    console.error(`Error building tree for ${dirPath}: ${err.message}`);
  }

  return lines;
}

async function combineFiles() {
  console.log('🚀 Combining code files (removing comments)...\n');
  
  const cwd = process.cwd();
  const isReact = isReactProject();
  const isPython = isPythonProject();
  
  if (isReact) {
    console.log('📦 Detected React project\n');
  }
  if (isPython) {
    console.log('🐍 Detected Python project\n');
  }
  if (!isReact && !isPython) {
    console.log('📁 Generic project\n');
  }

  try {
    console.log('Building directory tree...\n');
    const treeLines = await buildDirectoryTree(cwd);
    const treeContent = path.basename(cwd) + '/\n' + treeLines.join('\n');
    await fs.writeFile(OUTPUT_FILE, treeContent + SPACER);

    console.log('Collecting files...\n');
    const files = await collectReadableFiles(cwd);

    if (files.length === 0) {
      console.log('⚠️  No readable files found to combine');
      return;
    }

    console.log(`\n📂 Found ${files.length} files to combine\n`);

    let processedCount = 0;
    let commentRemovedCount = 0;

    for (const filePath of files) {
      try {
        const relativePath = path.relative(cwd, filePath);
        const content = await fs.readFile(filePath, 'utf8');
        
        const fileType = getFileType(path.basename(filePath));
        const processedContent = removeComments(content, fileType);
        
        if (fileType) {
          console.log(`  ✓ Including (comments removed): ${relativePath}`);
          commentRemovedCount++;
        } else {
          console.log(`  ✓ Including: ${relativePath}`);
        }
        
        const header = `==================== ${relativePath} ====================\n\n`;
        await fs.appendFile(OUTPUT_FILE, header + processedContent + SPACER);
        processedCount++;
      } catch (err) {
        const error = `!!!!!!!!!!!! ERROR reading ${filePath} !!!!!!!!!!!!\n${SPACER}`;
        await fs.appendFile(OUTPUT_FILE, error);
        console.error(`  ✗ Skipped ${filePath}: ${err.message}`);
      }
    }

    console.log(`\n✅ Done! Output saved to ${OUTPUT_FILE}`);
    console.log(`📊 Total files combined: ${processedCount}`);
    console.log(`💬 Files with comments removed: ${commentRemovedCount}`);
  } catch (err) {
    console.error(`\n🔥 Fatal error: ${err.message}`);
  }
}

combineFiles();