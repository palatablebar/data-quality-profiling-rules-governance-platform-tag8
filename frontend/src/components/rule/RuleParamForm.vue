<template>
  <div class="grid grid-cols-2 gap-x-4 gap-y-3">
    <div class="col-span-2">
      <div class="label mb-1">规则名</div>
      <input v-model="draft.name" class="input" placeholder="例如：证件号非空校验" />
    </div>
    <div>
      <div class="label mb-1">规则类型</div>
      <select v-model="draft.rule_type" class="input" @change="onTypeChange">
        <option v-for="type in RULE_TYPE_LIST" :key="type" :value="type">{{ RULE_TYPE_LABELS[type] }}</option>
      </select>
    </div>
    <div>
      <div class="label mb-1">严重度</div>
      <SeveritySelect v-model="draft.severity" />
    </div>
    <div class="col-span-2">
      <div class="label mb-1">校验列</div>
      <input v-model="draft.column_name" class="input" placeholder="从左侧列选择器点选" />
    </div>

    <template v-if="draft.rule_type === 'range'">
      <div>
        <div class="label mb-1">min</div>
        <input v-model="draft.min" class="input tabular-nums" placeholder="0" />
      </div>
      <div>
        <div class="label mb-1">max</div>
        <input v-model="draft.max" class="input tabular-nums" placeholder="50000000" />
      </div>
    </template>

    <div v-if="draft.rule_type === 'regex'" class="col-span-2">
      <div class="label mb-1">正则（整值匹配）</div>
      <input v-model="draft.pattern" class="input tabular-nums" placeholder="\d{18}" />
    </div>

    <div v-if="draft.rule_type === 'enum_set'" class="col-span-2">
      <div class="label mb-1">枚举值（逗号分隔）</div>
      <input v-model="draft.values" class="input" placeholder="A, I, D" />
    </div>

    <template v-if="draft.rule_type === 'referential'">
      <div>
        <div class="label mb-1">目标数据集 ID</div>
        <input v-model="draft.target_dataset_id" class="input tabular-nums" placeholder="机构字典 dataset_id" />
      </div>
      <div>
        <div class="label mb-1">目标列</div>
        <input v-model="draft.target_column" class="input" placeholder="branch_code" />
      </div>
    </template>

    <div v-if="draft.rule_type === 'expression'" class="col-span-2">
      <div class="label mb-1">表达式（白名单：> >= < <= == != and or not in abs len）</div>
      <input v-model="draft.expr" class="input tabular-nums" placeholder='balance > 0 and status in ["A","I"]' />
    </div>

    <div class="col-span-2">
      <div class="label mb-1">单规则样本上限</div>
      <input v-model.number="draft.sample_limit" type="number" min="1" max="5000" class="input tabular-nums" />
    </div>
    <div class="col-span-2 text-[11px] text-ink-soft">{{ RULE_TYPE_HINTS[draft.rule_type] }}</div>
  </div>
</template>

<script setup lang="ts">
import SeveritySelect from './SeveritySelect.vue'
import { RULE_TYPE_HINTS, RULE_TYPE_LABELS, RULE_TYPE_LIST } from '../../constants/ruleType'
import type { RuleDraft } from '../../types/rule'

const props = defineProps<{ draft: RuleDraft }>()

function onTypeChange() {
  // switching type resets the type-specific parameters
  props.draft.min = ''
  props.draft.max = ''
  props.draft.pattern = ''
  props.draft.values = ''
  props.draft.target_dataset_id = ''
  props.draft.target_column = ''
  props.draft.expr = ''
}
</script>
