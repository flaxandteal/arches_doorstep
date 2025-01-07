<script setup>
import { defineProps } from 'vue';
import Accordion from 'primevue/accordion';
import AccordionPanel from 'primevue/accordionpanel';
import AccordionHeader from 'primevue/accordionheader';
import AccordionContent from 'primevue/accordioncontent';
import DataTable from "primevue/datatable";
import Column from 'primevue/column';

const props = defineProps({
    successRows: Array,
    warningRows: Array,
    errorRows: Array,
    headers: Array
})

</script>
<template>
    <div>
        <Accordion multiple>
            <AccordionPanel value="0">
                <AccordionHeader>
                    <div class="header-container">
                        <div>Success</div>
                        <div>{{ successRows.length }}</div>
                    </div>
                </AccordionHeader>
                <AccordionContent>
                    <div>
                        <DataTable :value="successRows" scrollable scroll-height="250px" class="csv-mapping-table-container summary-tables">
                            <Column 
                                v-for="header in headers" 
                                :key="header" :field="header" 
                                :header="header" 
                            />
                        </DataTable>
                    </div>
                </AccordionContent>
            </AccordionPanel>
            <AccordionPanel value="1">
                <AccordionHeader>
                    <div class="header-container">
                        <div>Warnings</div>
                        <div>{{ warningRows.length }}</div>
                    </div>
                </AccordionHeader>
                <AccordionContent>
                    <div>
                        <DataTable :value="warningRows" scrollable scroll-height="250px" class="csv-mapping-table-container summary-tables">
                            <Column 
                                v-for="header in headers" 
                                :key="header" :field="header" 
                                :header="header" 
                            />
                        </DataTable>
                    </div>
                </AccordionContent>
            </AccordionPanel>
            <AccordionPanel value="3">
                <AccordionHeader>
                    <div class="header-container">
                        <div>Errors</div>
                        <div>{{ errorRows.length }}</div>
                    </div>
                </AccordionHeader>
                <AccordionContent>
                    <div>
                        <DataTable :value="errorRows" scrollable scroll-height="250px" class="csv-mapping-table-container summary-tables">
                            <Column 
                                v-for="header in headers" 
                                :key="header" :field="header" 
                                :header="header" 
                            />
                        </DataTable>
                    </div>
                </AccordionContent>
            </AccordionPanel>
        </Accordion>
    </div>
</template>

<style scoped>
.header-container{
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 2rem;
}
.summary-tables {
    max-height: 250px;
    margin-bottom: 4rem;
}
</style>