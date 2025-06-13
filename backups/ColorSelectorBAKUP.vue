<template>
  <div class="color-selector">
    <h2>Color Selector</h2>
    <table>
      <thead>
        <tr>
          <th>Type</th>
          <th>Color Class</th>
          <th>Select Color</th>
          <th>Preview</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="type in types" :key="type">
          <td>{{ type }}</td>
          <td>
            <v-select
              v-model="typeColors[type]"
              :items="safeVuetifyColorClasses"
              item-text="label"
              item-value="value"
              dense
              outlined
              hide-details
              style="width: 220px"
            >
              <template #item="{ item }">
                <div class="color-option">
                  <span :class="['color-dot', 'bg-' + (item.value || item)]"></span>
                  <span>{{ item.label || item }}</span>
                </div>
              </template>
            </v-select>
          </td>
          <td>
            <button @click="saveColor(type)">Save</button>
          </td>
          <td>
            <div :class="['preview-box', 'bg-' + typeColors[type]]"></div>
          </td>
        </tr>
        <tr>
          <td>Highlight</td>
          <td>
            <v-select
              v-model="typeColors['Highlight']"
              :items="safeVuetifyColorClasses"
              item-text="label"
              item-value="value"
              dense
              outlined
              hide-details
              style="width: 220px"
            >
              <template #item="{ item }">
                <div class="color-option">
                  <span :class="['color-dot', 'bg-' + (item.value || item)]"></span>
                  <span>{{ item.label || item }}</span>
                </div>
              </template>
            </v-select>
          </td>
          <td>
            <button @click="saveColor('Highlight')">Save</button>
          </td>
          <td>
            <div :class="['preview-box', 'bg-' + typeColors['Highlight']]"></div>
          </td>
        </tr>
        <tr>
          <td>DropLine</td>
          <td>
            <v-select
              v-model="typeColors['DropLine']"
              :items="safeVuetifyColorClasses"
              item-text="label"
              item-value="value"
              dense
              outlined
              hide-details
              style="width: 220px"
            >
              <template #item="{ item }">
                <div class="color-option">
                  <span :class="['color-dot', 'bg-' + (item.value || item)]"></span>
                  <span>{{ item.label || item }}</span>
                </div>
              </template>
            </v-select>
          </td>
          <td>
            <button @click="saveColor('DropLine')">Save</button>
          </td>
          <td>
            <div :class="['preview-box', 'bg-' + typeColors['DropLine']]"></div>
          </td>
        </tr>
      </tbody>
    </table>
    <v-select
      v-model="testColor"
      :items="safeVuetifyColorClasses"
      item-text="label"
      item-value="value"
      label="Test Color"
    />
  </div>
</template>

<script>
export default {
  data() {
    return {
      types: ['Advert', 'CTA', 'Promo', 'Segment', 'Trans'],
      typeColors: {},
      testColor: null,
      vuetifyColorClasses: [
        { label: 'Amber Lighten-4', value: 'amber lighten-4' },
        { label: 'Green Lighten-4', value: 'green lighten-4' },
        { label: 'Indigo Lighten-4', value: 'indigo lighten-4' },
        { label: 'Blue Lighten-4', value: 'blue lighten-4' },
        { label: 'Grey Lighten-4', value: 'grey lighten-4' },
        { label: 'Orange Lighten-2', value: 'orange lighten-2' },
        { label: 'Red Lighten-4', value: 'red lighten-4' },
        { label: 'Purple Lighten-4', value: 'purple lighten-4' },
        { label: 'Teal Lighten-4', value: 'teal lighten-4' },
        { label: 'Cyan Lighten-4', value: 'cyan lighten-4' },
        { label: 'Lime Lighten-4', value: 'lime lighten-4' },
        { label: 'Yellow Lighten-4', value: 'yellow lighten-4' },
        { label: 'Brown Lighten-4', value: 'brown lighten-4' },
        { label: 'Deep Orange Lighten-4', value: 'deep-orange lighten-4' },
        { label: 'Deep Purple Lighten-4', value: 'deep-purple lighten-4' },
        { label: 'Pink Lighten-4', value: 'pink lighten-4' },
        // Expand this list as needed for more options
      ],
    };
  },
  computed: {
    safeVuetifyColorClasses() {
      return this.vuetifyColorClasses.map(item => ({
        label: item.label || String(item.value),
        value: item.value
      }));
    }
  },
  methods: {
    saveColor(type) {
      localStorage.setItem(`color_${type}`, this.typeColors[type]);
      alert(`${type} color saved as ${this.typeColors[type]}`);
    },
  },
  created() {
    // Only load valid class names, never hex codes
    this.types.forEach(type => {
      const storedColor = localStorage.getItem(`color_${type}`);
      if (
        storedColor &&
        this.vuetifyColorClasses.some(c => c.value === storedColor)
      ) {
        this.typeColors[type] = storedColor;
      } else {
        this.typeColors[type] = this.vuetifyColorClasses[0].value;
      }
    });
    ['Highlight', 'DropLine'].forEach(effect => {
      const storedEffectColor = localStorage.getItem(`color_${effect}`);
      if (
        storedEffectColor &&
        this.vuetifyColorClasses.some(c => c.value === storedEffectColor)
      ) {
        this.typeColors[effect] = storedEffectColor;
      } else {
        this.typeColors[effect] = this.vuetifyColorClasses[0].value;
      }
    });
  },
};
</script>

<style scoped>
.color-selector {
  margin-top: 20px;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  border: 1px solid #ccc;
  padding: 8px;
}

th {
  background-color: #f2f2f2;
}

button {
  margin-left: 5px;
}

.preview-box {
  display: inline-block;
  width: 100px;
  height: 20px;
  border: 1px solid #aaa;
}

.color-option {
  display: flex;
  align-items: center;
}

.color-dot {
  display: inline-block;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  margin-right: 8px;
  border: 1px solid #888;
}
</style>
