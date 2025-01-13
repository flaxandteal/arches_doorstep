<script setup>
import Button from "primevue/button";
import Dropdown from "primevue/dropdown";
import InputSwitch from "primevue/inputswitch";
import Table from '../../components/Table.vue';
import { ref, onMounted, watch, computed } from "vue";
import arches from "arches";
import store from '../store/mainStore.js';
import errorStore from '../store/errorStore.js';
import Accordion from 'primevue/accordion';
import AccordionPanel from 'primevue/accordionpanel';
import AccordionHeader from 'primevue/accordionheader';
import AccordionContent from 'primevue/accordioncontent';  
import ToggleButton from 'primevue/togglebutton';
import Fuse from 'fuse.js'


const state = store.state;
const errorState = errorStore.state;
const languages = arches.languages;

let stringNodes = [];
let conceptNodes = [];
let resourceNodes = [];
let dateNodes = [];

const nodes = ref();
const langNodes = ref();
const csvBody = ref();
const headers = ref();
const numOfCols = ref();
const numOfRows = ref();
const csvExample = ref();
const columnHeaders = ref([]);
const dataSummary = ref({});

const accordionValue = computed(() => {
    return state.selectedResourceModel ? "0" : null;
});

const ready = computed(() => {
    return state.selectedResourceModel && state.fieldMapping?.find((v) => v.node);
});

// checks for duplicate nodes and prefixes the nodegroup
const updateNodeNames = (nodes) => {
    const nameMap = new Map();

    // First pass: count occurrences of each name
    nodes.forEach(node => {
        if (nameMap.has(node.name)) {
            nameMap.set(node.name, nameMap.get(node.name) + 1);
        } else {
            nameMap.set(node.name, 1);
        }
    });

    // Second pass: update names if duplicates are found
    nodes.forEach(node => {
        if (nameMap.get(node.name) > 1) {
            node.name = `${node.nodegroupname} - ${node.name}`;
        }
    });

    return nodes;
};

watch(() => state.csvArray, async (val) => {
    if(state.csvArray.length === 0) {
        return
    }
    numOfRows.value = val.length;
    numOfCols.value = val[0].length;
    if (state.hasHeaders) {
        columnHeaders.value = null;
        csvBody.value = val;
    } else {
        columnHeaders.value = val[0];
        csvBody.value = val.slice(1);
    }
});

watch(() => state.selectedResourceModel, (graph) => {
    if (graph) {
        state.selectedResourceModel = graph;
        const data = {"graphid": graph.graphid};
        store.submit("get_nodes", data).then((response) => {
            let theseNodes = response.result.map((node) => ({
                ...node,
                label: node.alias,
            }));
            langNodes.value = theseNodes.reduce((acc, node) => {
                if (node.datatype === "string") {
                    acc.push(node.alias);
                }
                return acc;
            }, []);
            stringNodes = theseNodes.filter((node) => {
                if (node.datatype === "string" || node.datatype === 'url') {
                    return node
                }
            });
            conceptNodes = theseNodes.filter((node) => {
                if (node.datatype === "concept" || node.datatype === "concept-list") {
                    return node
                }
            });
            resourceNodes = theseNodes.filter((node) => {
                if (node.datatype === "resource-instance") {
                    return node
                }
            });
            dateNodes = theseNodes.filter((node) => {
                if (node.datatype === "date") {
                    return node
                }
            });
            theseNodes = updateNodeNames(theseNodes)
            // theseNodes.unshift({
            //     alias: "resourceid",
            //     label: arches.translations.idColumnSelection,
            // });
            nodes.value = theseNodes;
        });
    }
});

watch(columnHeaders, async (headers) => {
    if (headers) {
        state.fieldMapping = headers.map(function (header) {
            return {
                field: header,
                node: ref(),
                checked: ref(false),
                datatype: ref(null),
                language: ref(
                    arches.languages.find(
                        (lang) => lang.code == arches.activeLanguage
                    )
                ),
            };
        });
    }
});

watch(() => state.hasHeaders, async (val) => {
    headers.value = null;
    if (val) {
        headers.value = state.csvArray[0];
        csvBody.value = state.csvArray;
    } else {
        headers.value = Array.apply(0, Array(state.csvArray[0].length)).map(
            function (_, b) {
                return b + 1;
            }
        );
        csvBody.value = state.csvArray.slice(1);
    }
});

watch(() => state.selectedResourceModel, (graph) => {
    if (!graph) {
        nodes.value = null;
    }
});

watch(csvBody, async (val) => {
    numOfRows.value = val.length;
    csvExample.value = val.slice(0, 5);
});

const formatSize = function (size) {
    var bytes = size;
    if (bytes == 0) return "0 Byte";
    var k = 1024;
    var dm = 2;
    var sizes = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"];
    var i = Math.floor(Math.log(bytes) / Math.log(k));
    return (
        "<strong>" +
        parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) +
        "</strong> " +
        sizes[i]
    );
};

const getNodeOptions = (mapping) => {
    if(!mapping.checked){
        return nodes.value
    }
    switch (mapping.datatype) {
        case 'string' || 'url':
            return stringNodes
        case 'concept-list' || 'concept':
            return conceptNodes
        case 'date':
            return dateNodes
        case 'resource-instance':
            return resourceNodes
        default:
            return nodes.value;
    }
};

const process = async () => {
    state.isLoading = true;
    const data = {
        file: state.file,
        data: JSON.stringify({ 
            mapping: state.fieldMapping,
            graph: {
                id: state.selectedResourceModel.graphid,
                name: state.selectedResourceModel.name
            }
        })
    };
    try {
        const response = await store.submit("process", data);
        // update store errors
        errorState.errorCounts = response.result.counts;
        errorState.totalErrors = response.result["error-count"];
        errorState.infoTable = response.result.tables[0].informations;
        errorState.errorTable = response.result.tables[0].errors;
        errorState.warningTable = response.result.tables[0].warnings;
        errorStore.updateTables();
        store.setDetailsTab('errors');
    } catch (error) {
        console.log(`Error Processing Data ${error}`);
    } finally {
        state.isLoading = false;
    }
}

const fuzzySearch = (list, pattern) => {
    const fuse = new Fuse(list, {
        keys: ['name'],
        threshold: 0.3,
        ignoreLocation: true
    })
    const result = fuse.search(pattern)
    return result
}

const autoSelectNodes = () => {
    state.fieldMapping.forEach(mapping => {
        const closestMatch = fuzzySearch(nodes.value, mapping.field);
        if (closestMatch.length > 0) {
            mapping["node"] = closestMatch[0].item.alias
            mapping.checked = true;
            updateDataType(mapping)
            getNodeOptions(mapping)    
        }
    })
}

// this is separated to work with auto select and manual dropdown change
const updateDataType = (mapping) => {
    const node = nodes.value.find(object => object.alias === mapping.node);
    if (node){
        mapping.datatype = node.datatype;
    }  
}
</script>

<template>
    <div class="import-single-csv-container">
        <div 
            v-if="state.file"
            class="import-single-csv-component-container"
        >
            <div 
                style="box-shadow: none"
            >
                <div class="title-text">
                    <h4>File Summary</h4>
                </div>
                <div>
                    <div>
                        <span class="etl-loading-metadata-key">File Name:</span>
                        <span class="etl-loading-metadata-value">{{
                            state.fileInfo.name
                        }}</span>
                    </div>
                    <div>
                        <span class="etl-loading-metadata-key">File Size:</span>
                        <span 
                            class="etl-loading-metadata-value"
                            v-html="formatSize(state.fileInfo.size)"
                        /> 
                    </div>
                    <div>
                        <span class="etl-loading-metadata-key">
                            Number of Rows:
                        </span>
                        <span class="etl-loading-metadata-value">{{
                            numOfRows
                        }}</span>
                    </div>
                    <div>
                        <span class="etl-loading-metadata-key">
                            Number of Columns:
                        </span>
                        <span class="etl-loading-metadata-value">{{
                            numOfCols
                        }}</span>
                    </div>
                </div>
            </div>
        </div>

        <div
            v-if="state.file"
            class="import-single-csv-component-container"
            style="margin: 20px"
        >
            <h4>Target Model</h4>
            <Dropdown
                v-model="state.selectedResourceModel"
                :options="state.graphModels"
                option-label="name"
                placeholder="Select a Resource Model"
                class="w-full md:w-14rem target-model-dropdown"
            />
            <Accordion :value="accordionValue" class="full-width">
                <AccordionPanel value="0">
                    <AccordionHeader>Advanced Summary</AccordionHeader>
                        <AccordionContent>
                            <div>
                                <h4>Data Summary</h4>
                                <Table 
                                    :headers = "state.dataSummary.columnHeaders"
                                    :rows = "state.dataSummary.rows" 
                                />
                            </div>
                        </AccordionContent>
                </AccordionPanel>
            </Accordion>
        </div>
        <div
            v-if="state.file && state.selectedResourceModel"
            class="import-single-csv-component-container"
            style="margin: 20px"
        >
            <h4 style="margin-bottom: 15px">
                Import Details
            </h4>
            <div
                class="card flex justify-content-center"
                style="display: flex; align-items: baseline"
            >
                <InputSwitch v-model="state.hasHeaders" />
                <p class="content-text">
                    Column names in the first row
                </p>
            </div>
        </div>
        <div
            v-if="state.file && state.selectedResourceModel"
            class="import-single-csv-component-container"
            style="margin: 20px"
        >
            <div>
                <Button 
                    label="Auto-Select Nodes" 
                    @click="autoSelectNodes" 
                    :disabled="!nodes"
                    size="large" 
                    class="btn-med"
                />
            </div>
            <div class="csv-mapping-table-container">
                <table class="table table-striped csv-mapping-table">
                    <thead>
                        <tr
                            v-if="nodes"
                        >
                            <th
                                v-for="(mapping, index) in state.fieldMapping" 
                                :key="index"
                                style="
                                    border-bottom: 1px solid #ddd;
                                    vertical-align: top;
                                "
                            >
                                <div class="flex space-between">
                                    <Dropdown
                                        v-model="mapping.node"
                                        :options="getNodeOptions(mapping)"
                                        option-label="name"
                                        option-value="alias"
                                        placeholder="Select a Node"
                                        @update:modelValue="(alias) => updateDataType(mapping)"
                                    />
                                    <ToggleButton v-model="mapping.checked" class="w-24" onLabel="filtered" offLabel="all" />
                                </div>
                                <Dropdown
                                    v-if="langNodes.includes(mapping.node)"
                                    v-model="mapping.language"
                                    :options="languages"
                                    :option-label="
                                        function (item) {
                                            return (
                                                item.name +
                                                ' (' +
                                                item.code +
                                                ')'
                                            );
                                        }
                                    "
                                />
                            </th>
                        </tr>
                    </thead>
                    <thead>
                        <tr class="column-names">
                            <th
                                v-for="(col, index) in columnHeaders" 
                                :key="index"
                                style="border-bottom: 1px solid #ddd"
                            >
                                {{ col }}
                            </th>
                        </tr>
                    </thead>

                    <tbody>
                        <tr 
                            v-for="(row, index) in csvExample" 
                            :key="index"
                        >
                            <td
                                v-for="(cell, child_index) in row"
                                :key="child_index"
                                style="vertical-align: text-top"
                            >
                                {{ cell }}
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
            <div 
            class="margin-top" 
            >
                <Button 
                    :disabled="!ready" 
                    label="Process" 
                    @click="process" 
                    size="large"
                    class="btn-large"
                />
            </div>
        </div>
        
    </div>
</template>

<style scoped>
.p-dropdown-items-wrapper {
    max-height: 100% !important;
}

.flex {
    display: flex;
    align-items: center;
}

.space-between {
    justify-content: space-between;
}

.margin-top {
    margin-top: 1rem;
}

.btn-med {
    font-size: 1.2rem;
}

.btn-large {
    font-size: 1.4rem;
}

.import-single-csv-container {
    position: relative;
    display: flex;
    flex-direction: column;
    align-content: flex-start;
    align-items: flex-start;
    overflow-y: scroll;
    height: 80vh;
}

.import-single-csv-component-container {
    width: fit-content;
    margin-left: 20px;
}
.title-text {
    font-size: 1.5rem;
    font-weight: 700;
}
.target-model-dropdown {
    width: 500px;
    margin-bottom: 4rem;
}
.content-text {
    font-size: 1.5rem;
    font-weight: 100;
    margin-left: 20px;
}
input[type=file] {
    display: none;
}
.summary-tables {
    max-height: 250px;
    margin-bottom: 4rem;
}
.full-width {
    width: 94vw
}
</style>
