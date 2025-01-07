<template>
    <div class="table-container">
        <table class="custom-table">
            <thead>
                <tr>
                    <th v-for="header in headers" :key="header">{{ header }}</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="row in rows" :key="row.id">
                    <td v-for="header in headers" :key="header">{{ row[header] }}</td>
                </tr>
            </tbody>
        </table>
    </div>
</template>

<script setup>
const props = defineProps({
    title: {
        type: String,
        required: true
    },
    headers: {
        type: Array,
        required: true
    },
    rows: {
        type: Array,
        required: true
    }
});
</script>

<style scoped>
.table-container {
    margin-bottom: 1rem;
    max-height: 280px;
    overflow-y: auto;
    border: 1px solid #ddd;
}

.custom-table {
    width: 100%;
    border-collapse: collapse;
}

.custom-table th, .custom-table td {
    padding: 8px;
    border: none; 
}

.custom-table th {
    background-color: #fff;
    text-align: left;
    position: sticky;
    top: 0;
    z-index: 1;
    border-bottom: 1px solid #ddd;
}

.custom-table tbody tr {
    background-color: #fff;
    border-bottom: 1px solid #ddd;
}

.custom-table tbody tr:hover {
    background-color: #ececec;
}
</style>