<script setup>
import { defineProps } from 'vue';
import Accordion from 'primevue/accordion';
import AccordionPanel from 'primevue/accordionpanel';
import AccordionHeader from 'primevue/accordionheader';
import AccordionContent from 'primevue/accordioncontent';
import DataTable from "primevue/datatable";
import Column from 'primevue/column';

const props = defineProps({
    conceptSuccessRows: Array,
    conceptWarningRows: Array,
    conceptErrorRows: Array,
    conceptHeaders: Array
})
</script>
<template>
    <div>
        <Accordion>
            <AccordionPanel>
                <AccordionHeader>
                    <div class="header-container">
                        <div>Success</div>
                        <div>{{ conceptSuccessRows.length }}</div>
                    </div>
                </AccordionHeader>
                <AccordionContent>
                    <div>
                        <DataTable :value="conceptSuccessRows" scrollable scroll-height="250px" class="csv-mapping-table-container summary-tables">
                            <Column 
                                v-for="header in conceptHeaders" 
                                :key="header" :field="header" 
                                :header="header" 
                            />
                        </DataTable>
                    </div>
                </AccordionContent>
            </AccordionPanel>
            <AccordionPanel>
                <AccordionHeader>
                    <div class="header-container">
                        <div>Warnings</div>
                        <div>{{ conceptWarningRows.length }}</div>
                    </div>
                </AccordionHeader>
                <AccordionContent>
                    <div>
                        <DataTable :value="conceptWarningRows" scrollable scroll-height="250px" class="csv-mapping-table-container summary-tables">
                            <Column 
                                v-for="header in conceptHeaders" 
                                :key="header" :field="header" 
                                :header="header" 
                            />
                        </DataTable>
                    </div>
                </AccordionContent>
            </AccordionPanel>
            <AccordionPanel>
                <AccordionHeader>
                    <div class="header-container">
                        <div>Errors</div>
                        <div>{{ conceptErrorRows.length }}</div>
                    </div>
                </AccordionHeader>
                <AccordionContent>
                    <div>
                        <DataTable :value="conceptErrorRows" scrollable scroll-height="250px" class="csv-mapping-table-container summary-tables">
                            <Column 
                                v-for="header in conceptHeaders" 
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
</style>