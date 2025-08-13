#!/usr/bin/env node

/**
 * Script to automatically update COMPONENT_MAP.md with current component information
 * Usage: node update-component-map.js
 */

const fs = require('fs');
const path = require('path');

// Configuration
const CONFIG = {
  rootDir: __dirname,
  componentsDir: path.join(__dirname, 'src/components'),
  viewsDir: path.join(__dirname, 'src/views'),
  mapFile: path.join(__dirname, 'COMPONENT_MAP.md'),
  ignore: ['node_modules', '.git', 'dist', 'public']
};

// Component tracking
const components = {
  views: {},
  settings: {},
  modals: {},
  core: {},
  imports: new Map()
};

/**
 * Get file size in lines
 */
function getFileStats(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    const lines = content.split('\n').length;
    const sizeKB = (fs.statSync(filePath).size / 1024).toFixed(1);
    return { lines, sizeKB };
  } catch (error) {
    return { lines: 0, sizeKB: 0 };
  }
}

/**
 * Extract component dependencies from Vue file
 */
function extractDependencies(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    const deps = {
      imports: [],
      props: [],
      emits: [],
      uses: []
    };

    // Extract imports
    const importRegex = /import\s+(?:{[^}]+}|\w+)\s+from\s+['"]([^'"]+)['"]/g;
    let match;
    while ((match = importRegex.exec(content)) !== null) {
      if (match[1].includes('.vue')) {
        deps.imports.push(match[1]);
      }
    }

    // Extract props (both Options API and Composition API)
    const propsRegex = /props:\s*{([^}]+)}|defineProps\(({[^}]+}|\[[^\]]+\])\)/g;
    while ((match = propsRegex.exec(content)) !== null) {
      const propsContent = match[1] || match[2];
      if (propsContent) {
        const propNames = propsContent.match(/['"]?(\w+)['"]?\s*:/g);
        if (propNames) {
          deps.props = propNames.map(p => p.replace(/['":]/g, '').trim());
        }
      }
    }

    // Extract emits
    const emitsRegex = /emits:\s*\[([^\]]+)\]|defineEmits\(\[([^\]]+)\]\)/g;
    while ((match = emitsRegex.exec(content)) !== null) {
      const emitsContent = match[1] || match[2];
      if (emitsContent) {
        const emitNames = emitsContent.match(/['"]([^'"]+)['"]/g);
        if (emitNames) {
          deps.emits = emitNames.map(e => e.replace(/['"]/g, ''));
        }
      }
    }

    return deps;
  } catch (error) {
    console.error(`Error extracting dependencies from ${filePath}:`, error.message);
    return { imports: [], props: [], emits: [], uses: [] };
  }
}

/**
 * Scan directory for Vue components
 */
function scanDirectory(dir, category) {
  if (!fs.existsSync(dir)) return;

  const files = fs.readdirSync(dir);
  
  files.forEach(file => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    
    if (stat.isDirectory() && !CONFIG.ignore.includes(file)) {
      // Recursively scan subdirectories
      const subCategory = category === 'components' && file === 'settings' ? 'settings' :
                         category === 'components' && file === 'modals' ? 'modals' :
                         category;
      scanDirectory(filePath, subCategory);
    } else if (file.endsWith('.vue')) {
      const stats = getFileStats(filePath);
      const deps = extractDependencies(filePath);
      const componentName = file;
      
      const componentInfo = {
        name: componentName,
        path: path.relative(CONFIG.rootDir, filePath),
        lines: stats.lines,
        sizeKB: stats.sizeKB,
        ...deps
      };

      // Categorize component
      if (category === 'views') {
        components.views[componentName] = componentInfo;
      } else if (category === 'settings') {
        components.settings[componentName] = componentInfo;
      } else if (category === 'modals') {
        components.modals[componentName] = componentInfo;
      } else {
        components.core[componentName] = componentInfo;
      }
    }
  });
}

/**
 * Generate markdown content for component map
 */
function generateMarkdown() {
  let md = `# Vue Component Map

This file provides a hierarchical map of Vue components and their relationships in the Show-Build frontend application.

*Last updated: ${new Date().toISOString().split('T')[0]}*

## Component Statistics

- **Total Components**: ${Object.keys({...components.views, ...components.settings, ...components.modals, ...components.core}).length}
- **Views**: ${Object.keys(components.views).length}
- **Settings Components**: ${Object.keys(components.settings).length}
- **Modal Components**: ${Object.keys(components.modals).length}
- **Core Components**: ${Object.keys(components.core).length}

## Component Hierarchy

### Views (Primary Routes)
\`\`\`
src/views/
`;

  // Add views
  Object.values(components.views).forEach(comp => {
    md += `├── ${comp.name} (${comp.lines} lines)\n`;
    if (comp.imports.length > 0) {
      comp.imports.forEach((imp, idx) => {
        const isLast = idx === comp.imports.length - 1;
        md += `│   ${isLast ? '└' : '├'}── Uses: ${path.basename(imp)}\n`;
      });
    }
    if (comp.props.length > 0) {
      md += `│   └── Props: ${comp.props.join(', ')}\n`;
    }
    md += `│\n`;
  });

  md += `\`\`\`

### Settings Components
\`\`\`
src/components/settings/
`;

  // Add settings components
  Object.values(components.settings).forEach(comp => {
    md += `├── ${comp.name} (${comp.lines} lines)\n`;
    if (comp.props.length > 0) {
      md += `│   ├── Props: ${comp.props.join(', ')}\n`;
    }
    if (comp.emits.length > 0) {
      md += `│   ├── Emits: ${comp.emits.join(', ')}\n`;
    }
    md += `│\n`;
  });

  md += `\`\`\`

### Modal Components
\`\`\`
src/components/modals/
`;

  // Add modal components
  Object.values(components.modals).forEach(comp => {
    md += `├── ${comp.name}\n`;
  });

  md += `\`\`\`

### Core Components
\`\`\`
src/components/
`;

  // Add core components
  Object.values(components.core).forEach(comp => {
    md += `├── ${comp.name} (${comp.lines} lines)\n`;
  });

  md += `\`\`\`

## File Size Analysis

### Large Files (>1000 lines)
`;

  // Find large files
  const allComponents = {...components.views, ...components.settings, ...components.modals, ...components.core};
  const largeFiles = Object.values(allComponents)
    .filter(c => c.lines > 1000)
    .sort((a, b) => b.lines - a.lines);

  largeFiles.forEach(comp => {
    md += `- ${comp.name}: ${comp.lines} lines (${comp.sizeKB} KB)\n`;
  });

  md += `
### Recently Extracted Components
`;

  // List settings components as recently extracted
  Object.values(components.settings).forEach(comp => {
    md += `- ✅ ${comp.name}: ${comp.lines} lines\n`;
  });

  md += `
## Component Dependencies

### Import Graph
\`\`\`mermaid
graph TD
`;

  // Generate simple dependency graph for views
  Object.values(components.views).forEach(view => {
    view.imports.forEach(imp => {
      const importName = path.basename(imp);
      md += `    ${view.name} --> ${importName}\n`;
    });
  });

  md += `\`\`\`

## Notes

- Components marked with ✅ have been successfully refactored
- File sizes are approximate and may vary with formatting
- This map is auto-generated - run \`node update-component-map.js\` to update
`;

  return md;
}

/**
 * Main execution
 */
function main() {
  console.log('🔍 Scanning Vue components...');
  
  // Scan directories
  scanDirectory(CONFIG.viewsDir, 'views');
  scanDirectory(path.join(CONFIG.componentsDir, 'settings'), 'settings');
  scanDirectory(path.join(CONFIG.componentsDir, 'modals'), 'modals');
  scanDirectory(CONFIG.componentsDir, 'components');
  
  console.log(`📊 Found ${Object.keys({...components.views, ...components.settings, ...components.modals, ...components.core}).length} components`);
  
  // Generate markdown
  const markdown = generateMarkdown();
  
  // Write to file
  fs.writeFileSync(CONFIG.mapFile, markdown);
  console.log(`✅ Component map updated: ${CONFIG.mapFile}`);
  
  // Print summary
  console.log('\n📈 Summary:');
  console.log(`  Views: ${Object.keys(components.views).length}`);
  console.log(`  Settings: ${Object.keys(components.settings).length}`);
  console.log(`  Modals: ${Object.keys(components.modals).length}`);
  console.log(`  Core: ${Object.keys(components.core).length}`);
}

// Run the script
main();