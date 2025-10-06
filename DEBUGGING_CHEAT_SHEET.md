# 🔧 Show-Build Debugging Cheat Sheet

## 🚨 STEP 1: IMMEDIATE (30 sec)
```bash
./scripts/debug-frontend.sh
```

## 🔍 STEP 2: BROWSER CHECK (1 min)
- **DevTools → Console**: Look for errors/warnings
- **DevTools → Network**: Check for failed requests (red entries)
- **Vue DevTools**: Inspect component state

## 🎯 STEP 3: COMMON FIXES (2 min)

### Template Ref Conflicts (90% of form issues)
```bash
# Check:
cd disaffected-ui/src && grep -rn 'ref="[^"]*"' . | sed 's/.*ref="\([^"]*\)".*/\1/' | sort | uniq -d

# Fix: Rename refs with 'Ref' suffix
<v-form ref="episodeFormRef">  <!-- was ref="episodeForm" -->
```

### API Issues
```bash
# Test endpoints:
curl http://localhost:8888/api/episodes/next-number
curl http://localhost:8888/api/episodes/templates
```

### Services Down
```bash
# Backend:
docker compose up --build server

# Frontend:
cd disaffected-ui && npm run serve
```

### Vuetify Text Clipping (Text faded/cut off at top)
```css
/* In component styles: */
.your-textarea :deep(.v-field),
.your-textarea :deep(.v-field__input),
.your-textarea :deep(textarea) {
  clip-path: none !important;
  mask: none !important;
  -webkit-mask: none !important;
  overflow: visible !important;
}
```
**Cause**: Vuetify applies CSS masks/clip-paths that cut off text at container edges

## 📝 QUICK REFERENCE

**Template Refs**: Always end with `Ref`
- ✅ `formRef`, `dialogRef`, `tableRef`  
- ❌ `form`, `dialog`, `table`

**Reactive Variables**: Different descriptive names
- ✅ `formData`, `dialogVisible`, `tableItems`
- ❌ `form`, `dialog`, `table`

**Common Symptoms → Likely Cause**:
- Form resets mysteriously → Template ref conflict
- Data loads then disappears → Template ref conflict  
- API calls fail silently → Network/endpoint issue
- Components not updating → Reactivity/v-model issue

## 🔗 FULL DOCS
- [`DEBUG_FIRST.md`](DEBUG_FIRST.md) - Priority debugging
- [`docs/DEBUGGING_STANDARDS.md`](docs/DEBUGGING_STANDARDS.md) - Complete guide
- [`CLAUDE.md`](CLAUDE.md) - Project overview