# 🚨 DEBUG FIRST - PRIORITY REFERENCE

**⚠️ START HERE FOR ANY FRONTEND ISSUE ⚠️**

## 🔥 IMMEDIATE ACTION (30 seconds)

```bash
# Run this FIRST for any unexplained frontend issue:
./scripts/debug-frontend.sh
```

## 📋 CRITICAL CHECKLIST (Must check EVERY time)

### 1. Template Ref Naming Conflicts ⭐ **MOST COMMON - CAUSES 80% OF VUE ISSUES**
**Symptoms**: Components fail to mount, modals open then close immediately, dropdowns show "no data available", form resets mysteriously, reactivity breaks without obvious cause

**📖 COMPLETE GUIDE**: [`docs/VUE_TEMPLATE_REF_CONFLICTS.md`](docs/VUE_TEMPLATE_REF_CONFLICTS.md)

```bash
# Quick automated check:
./scripts/debug-frontend.sh  # Scans for ALL ref conflicts
```
**Fix**: Rename conflicting refs to end with `Ref` (e.g., `formRef`, `dialogRef`)

### 2. Vue DevTools Console Check ⭐ **CRITICAL**
1. Open browser DevTools → **Console tab**
2. Look for:
   - `Uncaught Promise rejections`
   - `Vue reactivity warnings`  
   - `Component lifecycle errors`
   - `Network 404/500 errors`

### 3. API Connectivity ⭐ **BLOCKING ISSUE**
```bash
# Test key endpoints:
curl -s http://localhost:8888/api/episodes/next-number | jq .
curl -s http://localhost:8888/api/episodes/templates | jq .
```

### 4. Network Tab Check ⭐ **SILENT FAILURES**
- Browser DevTools → **Network tab**
- Look for failed requests (red entries)
- Check response data format

## 🎯 RESOLUTION PRIORITY

**99% of frontend issues fall into these patterns:**

1. **Template ref naming conflicts** → Rename refs with `Ref` suffix
2. **API endpoint issues** → Field name mismatches (e.g., `next_number` vs `next_episode_number`)
3. **Vuetify component binding** → v-model conflicts or wrong item-value props
4. **Async data race conditions** → Add proper loading states and delays

## ⏱️ TIME-SAVING RULES

- **Before debugging**: Run `./scripts/debug-frontend.sh` (saves 10+ minutes)
- **Before asking for help**: Check this file first
- **Before deep diving**: Fix any conflicts found by the script
- **Before adding console.logs**: Use Vue DevTools first

## 📚 FULL DOCUMENTATION

- **Complete Guide**: [`docs/DEBUGGING_STANDARDS.md`](docs/DEBUGGING_STANDARDS.md)
- **Project Overview**: [`CLAUDE.md`](CLAUDE.md)

---
**💡 Pro Tip**: Bookmark this file - it will save hours of debugging time!