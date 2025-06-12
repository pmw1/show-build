<template>
  <div class="color-selector">
    <h2>Color Selector</h2>
    <table>
      <thead>
        <tr>
          <th>Type</th>
          <th>Color</th>
          <th>Select Color</th>
          <th>Preview</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(type, index) in types" :key="index">
          <td>{{ type }}</td>
          <td>
            <input
              type="text"
              v-model="typeColors[type]"
              placeholder="Enter color hex code or name"
            />
          </td>
          <td>
            <button @click="openColorPicker(type)">Select Color</button>
          </td>
          <td>
            <div :style="{ backgroundColor: typeColors[type], width: '100px', height: '20px' }"></div>
          </td>
        </tr>
        <tr>
          <td>Highlight</td>
          <td>
            <input
              type="text"
              id="row-highlight"
              v-model="typeColors['Highlight']"
              placeholder="Enter color hex code or name"
            />
          </td>
          <td>
            <button @click="openColorPicker('Highlight')">Select Color</button>
          </td>
          <td>
            <div :style="{ backgroundColor: typeColors['Highlight'], width: '100px', height: '20px' }"></div>
          </td>
        </tr>
        <tr>
          <td>DropLine</td>
          <td>
            <input
              type="text"
              id="drop-line"
              v-model="typeColors['DropLine']"
              placeholder="Enter color hex code or name"
            />
          </td>
          <td>
            <button @click="openColorPicker('DropLine')">Select Color</button>
          </td>
          <td>
            <div :style="{ backgroundColor: typeColors['DropLine'], width: '100px', height: '20px' }"></div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
export default {
  data() {
    return {
      types: ['Advert', 'CTA', 'Promo', 'Segment', 'Trans'],
      typeColors: {},
    };
  },
  methods: {
    saveColor(type) {
      localStorage.setItem(`color_${type}`, this.typeColors[type]);
      alert(`${type} color saved as ${this.typeColors[type]}`);
    },
    openColorPicker(type) {
      const picker = document.createElement('input');
      picker.type = 'color';
      picker.value = this.typeColors[type];
      picker.onchange = () => {
        this.typeColors[type] = picker.value;
        this.saveColor(type);
      };
      picker.click();
    },
  },
  created() {
    this.types.forEach(type => {
      const storedColor = localStorage.getItem(`color_${type}`);
      if (storedColor) {
        this.typeColors[type] = storedColor;
      }
    });
    ['Highlight', 'DropLine'].forEach(effect => {
      const storedEffectColor = localStorage.getItem(`color_${effect}`);
      if (storedEffectColor) {
        this.typeColors[effect] = storedEffectColor;
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

input[type="text"], button {
  margin-left: 5px;
}

div {
  display: inline-block;
}
</style>
