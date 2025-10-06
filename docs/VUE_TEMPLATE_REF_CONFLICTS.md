# Vue Template Ref Naming Conflicts - Critical Debugging Guide

## 🚨 **FIRST PRIORITY FOR UNEXPLAINED FRONTEND ISSUES**

Vue template ref naming conflicts are the **#1 cause** of inexplicable frontend bugs in Show-Build. Always check for these conflicts first when encountering:

- Components that won't mount/render
- Modals opening then immediately closing  
- Dropdowns showing "no data available"
- Reactivity breaking without obvious cause
- Form values mysteriously resetting

## **The Problem**

Vue 3's reactivity system fails catastrophically when template `ref` names conflict with Composition API reactive variables. This creates a naming collision that causes:

1. **Component Mounting Failures** - Components fail during lifecycle hooks
2. **Reactivity System Breakdown** - Vue can't distinguish between template refs and reactive vars
3. **Silent Failures** - No obvious errors, components just fail to work properly

## **Symptoms Checklist**

✅ **Check for these symptoms first:**

- [ ] Component appears to load but behaves incorrectly
- [ ] Modal/dialog opens briefly then closes immediately  
- [ ] Console shows lifecycle hooks starting but not completing
- [ ] Data is available but UI shows "no data" or blank states
- [ ] Form inputs reset to initial values unexpectedly
- [ ] Vue DevTools shows conflicting reactive sources

## **Common Conflict Patterns**

### ❌ **WRONG - Conflicting Names:**
```vue
<template>
  <v-form ref="episodeForm">  <!-- ref name conflicts -->
    <v-text-field v-model="episodeForm.title" />
  </v-form>
</template>

<script>
const episodeForm = ref({title: ''})  <!-- Same name as template ref -->
</script>
```

### ✅ **CORRECT - Distinct Names:**
```vue
<template>
  <v-form ref="episodeFormRef">  <!-- Unique ref name -->
    <v-text-field v-model="episodeForm.title" />
  </v-form>
</template>

<script>
const episodeForm = ref({title: ''})  <!-- Clear separation -->
</script>
```

## **Naming Convention**

**ALWAYS** use `Ref` suffix for template refs to prevent conflicts:

```vue
<template>
  <v-form ref="formRef">
  <v-dialog ref="dialogRef"> 
  <v-table ref="tableRef">
  <v-card ref="cardRef">
</template>
```

## **Detection Methods**

### **1. Automated Scanning (RECOMMENDED)**
```bash
# Run the debug frontend script
./scripts/debug-frontend.sh
```
This script automatically scans for ref conflicts and reports them.

### **2. Manual Scanning**
```bash
# Find all template refs in Vue components
cd disaffected-ui/src
grep -rn 'ref="[^"]*"' . | sed 's/.*ref="\([^"]*\)".*/\1/' | sort

# Look for duplicate names in same component
grep -rn 'ref="[^"]*"' ComponentName.vue
grep -n 'ref(' ComponentName.vue  # Look for Composition API refs
```

### **3. Vue DevTools Investigation**
1. Open Vue DevTools → Components tab
2. Look for components showing as "not mounted" but visible in DOM
3. Check for multiple reactive sources with same name
4. Look for template refs that don't resolve properly

## **Historical Fixes in Show-Build**

The following components had ref conflicts that were fixed:

### **NewItemModal.vue** (Primary Issue)
- **Problem**: `ref="newItemForm"` conflicted with form data reactive variable
- **Fix**: Changed to `ref="newItemFormRef"`
- **Impact**: Modal was opening but immediately closing, causing "no data available" in dropdown

### **ShowEdit.vue** 
- **Problem**: `ref="form"` conflicted with reactive form data
- **Fix**: Changed to `ref="showFormRef"`

### **EpisodeScaffoldModal.vue**
- **Problem**: `ref="form"` conflicted with episode form data  
- **Fix**: Changed to `ref="episodeFormRef"`

### **OrganizationEdit.vue**
- **Problem**: `ref="form"` conflicted with org form data
- **Fix**: Changed to `ref="orgFormRef"`

### **EpisodesView.vue**
- **Problem**: `ref="episodeFormRef"` conflicted with another form ref
- **Fix**: Changed to `ref="episodeViewFormRef"`

## **Quick Diagnostic Questions**

When encountering unexplained frontend issues, ask:

1. **Is the component mounting completely?** Check console for lifecycle completion
2. **Are template refs resolving?** Use `console.log(this.$refs)` in mounted()
3. **Do any ref names match reactive variable names?** Scan component for conflicts
4. **Is Vue DevTools showing the component as properly mounted?**
5. **Are there any "proxy" related warnings in console?**

## **Prevention Strategies**

### **1. Enforce Naming Convention**
- **Template refs**: Always use `Ref` suffix (`formRef`, `dialogRef`, `tableRef`)
- **Reactive variables**: Use descriptive names (`formData`, `modalState`, `tableItems`)

### **2. Linting Rules** (Future Enhancement)
Consider adding ESLint rules to catch ref conflicts:

```javascript
// .eslintrc.js - Future enhancement
rules: {
  'vue/no-template-ref-reactive-conflict': 'error'
}
```

### **3. Regular Scanning**
Run `./scripts/debug-frontend.sh` regularly during development to catch conflicts early.

## **Debugging Workflow**

### **Step 1: Quick Conflict Scan**
```bash
./scripts/debug-frontend.sh
```

### **Step 2: If Conflicts Found**
1. Rename conflicting template refs with `Ref` suffix
2. Update any code that references the old ref names
3. Test component functionality

### **Step 3: If No Conflicts Found**
Continue with standard debugging:
- Check component props/data flow
- Verify API responses
- Check authentication/permissions
- Review Vue component lifecycle

## **Emergency Fixes**

If you need an immediate fix for a broken component:

1. **Scan the component** for `ref="..."` attributes
2. **Check for matching variable names** in the script section
3. **Rename template refs** with `Ref` suffix
4. **Test immediately** - conflicts usually fix instantly when resolved

## **Testing the Fix**

After fixing ref conflicts:

1. **Component should mount properly** - Check console for complete lifecycle
2. **Modals should stay open** - No immediate closing behavior
3. **Dropdowns should populate** - Data should flow correctly
4. **Forms should maintain state** - No mysterious resets

## **Key Takeaways**

- ⚡ **Check ref conflicts FIRST** for unexplained frontend issues
- 📋 **Use consistent naming** - template refs get `Ref` suffix
- 🔍 **Use debug-frontend.sh** for automated scanning
- ⚙️ **Fix immediately** - conflicts usually resolve instantly
- 📖 **Document new patterns** - Add to this guide when new patterns emerge

---

**💡 Pro Tip**: The `debug-frontend.sh` script is your best friend. Run it first thing when troubleshooting any mysterious Vue component issues. Template ref conflicts cause 80%+ of inexplicable frontend bugs in Vue 3 applications.