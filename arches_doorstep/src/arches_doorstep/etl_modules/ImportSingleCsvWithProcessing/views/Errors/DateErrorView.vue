<script setup>
import { defineProps, watch } from 'vue';
import DataTable from "primevue/datatable";
import Column from 'primevue/column';

const props = defineProps({
    dateRows: Array,
    dateHeaders: Array
})
</script>

<template>
    <div>
        <DataTable :value="props.dateRows" scrollable scroll-height="250px" class="csv-mapping-table-container summary-tables">
            <Column 
                v-for="header in dateHeaders" 
                :key="header" 
                :field="header" 
                :header="header" 
            />
        </DataTable>                 
    </div>
</template>

<style scoped>
.summary-tables {
    max-height: 250px;
    margin-bottom: 4rem;
}
</style>