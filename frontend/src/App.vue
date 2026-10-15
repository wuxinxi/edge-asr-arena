<template>
  <div class="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-500/30">
    <!-- 顶部导航栏 -->
    <header class="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-50 px-6 py-3.5 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <div class="h-9 w-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-sky-400 flex items-center justify-center shadow-lg shadow-indigo-500/20 text-white font-black text-lg">
          <Mic class="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 class="text-lg font-bold tracking-tight text-white flex items-center gap-2">
            edge-asr-arena
            <span class="text-xs font-medium px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              Mac 端侧 ASR 评测平台
            </span>
          </h1>
          <p class="text-xs text-slate-400">客观 CER/WER · 吵杂抗干扰 · 流式延迟 · 统一隔离环境</p>
        </div>
      </div>

      <!-- 硬件/系统监控简报 -->
      <div v-if="systemInfo" class="hidden md:flex items-center space-x-4 text-xs bg-slate-800/60 px-3.5 py-1.5 rounded-lg border border-slate-700/50">
        <div class="flex items-center gap-1.5 text-slate-300">
          <span class="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>{{ systemInfo.is_apple_silicon ? 'Apple Silicon' : systemInfo.machine }}</span>
        </div>
        <div class="text-slate-500">|</div>
        <div class="text-slate-300">
          内存: <span class="text-indigo-400 font-semibold">{{ systemInfo.memory_available_gb }}GB</span> 可用 / {{ systemInfo.memory_total_gb }}GB
        </div>
      </div>
    </header>

    <!-- 工作区切换 Tab -->
    <nav class="border-b border-slate-800 bg-slate-900/30 px-6 py-2 flex space-x-1 overflow-x-auto text-sm">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        @click="activeTab = tab.id"
        :class="[
          'px-3.5 py-1.5 rounded-lg font-medium transition-all flex items-center gap-2 whitespace-nowrap',
          activeTab === tab.id
            ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
        ]"
      >
        <component :is="tab.icon" class="w-4 h-4 shrink-0" />
        <span>{{ tab.name }}</span>
      </button>
    </nav>

    <!-- 主工作区内容 -->
    <main class="flex-1 p-6 max-w-7xl mx-auto w-full space-y-6">

      <!-- 1. 场景选型工作区 -->
      <section v-if="activeTab === 'scenario'" class="space-y-6">
        <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h2 class="text-xl font-bold text-white flex items-center gap-2">
              <Compass class="w-5 h-5 text-indigo-400" />
              <span>场景选型与模型矩阵</span>
            </h2>
            <p class="text-sm text-slate-400">根据实际业务需求快速筛选适合本地端侧运行的 ASR 候选模型</p>
          </div>
          <!-- 场景过滤器 -->
          <div class="flex flex-wrap gap-2 text-xs">
            <button
              v-for="tag in scenarioFilters"
              :key="tag.id"
              @click="toggleScenarioFilter(tag.id)"
              :class="[
                'px-3 py-1.5 rounded-md border transition-all',
                activeScenarioTag === tag.id
                  ? 'bg-indigo-500/20 border-indigo-500 text-indigo-300 font-semibold'
                  : 'bg-slate-800/40 border-slate-700/60 text-slate-400 hover:border-slate-600'
              ]"
            >
              {{ tag.name }}
            </button>
          </div>
        </div>

        <!-- 模型矩阵内容区域 -->
        <!-- 1. 加载中骨架屏 -->
        <div v-if="isLoadingModels" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          <div
            v-for="i in 6"
            :key="i"
            class="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 animate-pulse space-y-4"
          >
            <div class="flex justify-between items-center">
              <div class="h-5 w-32 bg-slate-800 rounded"></div>
              <div class="h-4 w-16 bg-slate-800 rounded-full"></div>
            </div>
            <div class="h-4 w-24 bg-slate-800/60 rounded"></div>
            <div class="h-14 bg-slate-950/60 rounded-xl border border-slate-800/60"></div>
            <div class="space-y-2">
              <div class="h-3.5 w-full bg-slate-800/40 rounded"></div>
              <div class="h-3.5 w-3/4 bg-slate-800/40 rounded"></div>
            </div>
            <div class="pt-3 border-t border-slate-800/60 flex justify-between items-center">
              <div class="h-4 w-20 bg-slate-800 rounded"></div>
              <div class="h-6 w-14 bg-slate-800 rounded-lg"></div>
            </div>
          </div>
        </div>

        <!-- 2. 加载失败提示 -->
        <div v-else-if="modelsError" class="bg-red-500/10 border border-red-500/30 rounded-2xl p-8 text-center space-y-3">
          <AlertCircle class="w-8 h-8 text-red-400 mx-auto" />
          <h4 class="text-base font-semibold text-red-300">模型列表加载失败</h4>
          <p class="text-xs text-slate-400 max-w-md mx-auto">{{ modelsError }}</p>
          <button
            @click="loadModels"
            class="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white text-xs font-medium transition-all shadow-md shadow-red-600/20"
          >
            <RefreshCw class="w-3.5 h-3.5" />
            <span>重新加载</span>
          </button>
        </div>

        <!-- 3. 无匹配结果提示 -->
        <div v-else-if="filteredModels.length === 0" class="bg-slate-900/60 border border-slate-800 rounded-2xl p-12 text-center space-y-3">
          <Compass class="w-8 h-8 text-slate-500 mx-auto" />
          <h4 class="text-base font-medium text-slate-300">未找到符合当前筛选条件的模型</h4>
          <p class="text-xs text-slate-500">当前分类下暂无模型，可切换标签或重置筛选查看所有模型</p>
          <button
            @click="activeScenarioTag = 'all'"
            class="px-3.5 py-1.5 rounded-lg bg-indigo-600/20 border border-indigo-500/40 text-indigo-300 text-xs font-medium hover:bg-indigo-600/30 transition-all"
          >
            重置为全部模型
          </button>
        </div>

        <!-- 4. 正常渲染模型矩阵卡片 -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          <div
            v-for="model in filteredModels"
            :key="model.key"
            class="group relative bg-gradient-to-b from-slate-900/90 via-slate-900/70 to-slate-950/90 border border-slate-800/80 hover:border-indigo-500/50 rounded-2xl p-5 hover:shadow-xl hover:shadow-indigo-500/10 transition-all duration-300 flex flex-col justify-between"
          >
            <div>
              <!-- 顶部标题与就绪状态 -->
              <div class="flex justify-between items-start gap-2 mb-2">
                <h3 class="font-bold text-base text-slate-100 group-hover:text-indigo-300 transition-colors tracking-tight leading-snug">
                  {{ model.name }}
                </h3>
                <span :class="[
                  'inline-flex items-center gap-1.5 text-[11px] font-medium px-2.5 py-0.5 rounded-full border shrink-0',
                  model.is_available
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                    : 'bg-amber-500/10 border-amber-500/30 text-amber-400'
                ]">
                  <span :class="['h-1.5 w-1.5 rounded-full', model.is_available ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400']"></span>
                  {{ model.is_available ? '权重就绪' : '待配置' }}
                </span>
              </div>

              <!-- 模型 Key 代码标签 -->
              <div class="mb-3.5">
                <span class="text-[11px] font-mono text-slate-400 bg-slate-950/70 px-2 py-0.5 rounded-md border border-slate-800/80 inline-block">
                  {{ model.key }}
                </span>
              </div>

              <!-- 3 列核心参数微卡片 (网格化) -->
              <div class="grid grid-cols-3 gap-2 py-2.5 px-3 bg-slate-950/40 rounded-xl border border-slate-800/60 mb-3.5 text-center">
                <div class="flex flex-col">
                  <span class="text-[10px] text-slate-500">参数量</span>
                  <span class="text-xs font-semibold text-slate-200 mt-0.5">{{ model.parameters }}</span>
                </div>
                <div class="flex flex-col border-x border-slate-800/60">
                  <span class="text-[10px] text-slate-500">体积</span>
                  <span class="text-xs font-semibold text-slate-200 mt-0.5">{{ model.download_size }}</span>
                </div>
                <div class="flex flex-col">
                  <span class="text-[10px] text-slate-500">许可证</span>
                  <span class="text-xs font-semibold text-slate-200 mt-0.5 truncate px-1" :title="model.license">{{ model.license }}</span>
                </div>
              </div>

              <!-- 特性参数列表 -->
              <div class="space-y-2 text-xs mb-4">
                <div class="flex justify-between items-center">
                  <span class="text-slate-400">流式支持:</span>
                  <span :class="[
                    'px-2 py-0.5 rounded text-[11px] font-medium border',
                    model.supports_streaming
                      ? 'bg-emerald-500/10 border-emerald-500/25 text-emerald-400'
                      : 'bg-slate-800/50 border-slate-700/60 text-slate-400'
                  ]">
                    {{ model.supports_streaming ? '支持' : '不支持' }}
                  </span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-slate-400">Mac 后端:</span>
                  <span class="text-[11px] font-medium text-indigo-300 bg-indigo-950/40 border border-indigo-500/20 px-2 py-0.5 rounded">
                    {{ model.mac_backend }}
                  </span>
                </div>
              </div>
            </div>

            <!-- 底部操作栏 -->
            <div class="pt-3.5 border-t border-slate-800/80 flex items-center justify-between text-xs">
              <div class="flex items-center gap-1.5 text-slate-400 font-mono text-[11px]">
                <span class="text-slate-500">环境:</span>
                <span class="bg-slate-950/80 px-1.5 py-0.5 rounded border border-slate-800 text-slate-300">
                  .venvs/{{ model.venv_name }}
                </span>
              </div>
              <button
                @click="jumpToExplore(model.key)"
                class="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-gradient-to-r from-indigo-600 to-sky-600 hover:from-indigo-500 hover:to-sky-500 text-white font-medium text-xs shadow-md shadow-indigo-600/20 hover:shadow-indigo-500/30 transition-all duration-200 group-hover:translate-x-0.5"
              >
                <span>体验</span>
                <span class="text-[10px]">→</span>
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- 2. 能力探索工作区 -->
      <section v-if="activeTab === 'explore'" class="space-y-6">
        <div>
          <h2 class="text-xl font-bold text-white flex items-center gap-2">
            <FlaskConical class="w-5 h-5 text-indigo-400" />
            <span>单音频能力探索</span>
          </h2>
          <p class="text-sm text-slate-400">上传本地音频或自录语音，体验单模型转写表现、时间戳及客观错误率计算</p>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <!-- 左侧配置与上传 -->
          <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
            <div>
              <label class="block text-xs font-semibold text-slate-400 mb-1.5">选择测试模型</label>
              <select v-model="exploreModelKey" class="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500">
                <option v-for="m in models" :key="m.key" :value="m.key">{{ m.name }} ({{ m.parameters }})</option>
              </select>
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-400 mb-1.5">主导语言</label>
              <select v-model="exploreLang" class="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500">
                <option value="zh">中文普通话 (zh)</option>
                <option value="en">英语 (en)</option>
                <option value="auto">自动识别</option>
              </select>
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-400 mb-1.5">参考标准文本 (用于自动计算 CER/WER，可选)</label>
              <textarea
                v-model="exploreRefText"
                rows="3"
                placeholder="在此填写真实文本，系统将对齐输出高亮差异..."
                class="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              ></textarea>
            </div>

            <div>
              <div class="flex justify-between items-center mb-2">
                <label class="block text-xs font-semibold text-slate-400">音频输入方式</label>
                <!-- 切换录音或文件上传 -->
                <div class="inline-flex rounded-lg border border-slate-700 bg-slate-800 p-0.5 text-[11px]">
                  <button
                    type="button"
                    @click="setAudioInputMode('upload')"
                    :class="[
                      'px-2.5 py-1 rounded-md font-medium transition-all flex items-center gap-1',
                      audioInputMode === 'upload' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                    ]"
                  >
                    <Upload class="w-3 h-3" />
                    <span>文件上传</span>
                  </button>
                  <button
                    type="button"
                    @click="setAudioInputMode('record')"
                    :class="[
                      'px-2.5 py-1 rounded-md font-medium transition-all flex items-center gap-1',
                      audioInputMode === 'record' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                    ]"
                  >
                    <Mic class="w-3 h-3" />
                    <span>麦克风录音</span>
                  </button>
                </div>
              </div>

              <!-- 模式 1: 文件上传 -->
              <div v-if="audioInputMode === 'upload'" class="space-y-1.5">
                <input
                  type="file"
                  ref="audioFileInput"
                  accept=".wav,.mp3,.flac,.m4a,.ogg,audio/*"
                  @change="handleFileUpload"
                  class="block w-full text-xs text-slate-400 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-500 cursor-pointer"
                />
                <p v-if="fileUploadError" class="mt-1.5 text-xs text-rose-400 flex items-center gap-1.5 bg-rose-500/10 p-2 rounded border border-rose-500/20">
                  <AlertCircle class="w-3.5 h-3.5 shrink-0" />
                  <span>{{ fileUploadError }}</span>
                </p>
                <p class="text-[10px] text-slate-500">仅限音频文件 (.wav, .mp3, .flac, .m4a)</p>
              </div>

              <!-- 模式 2: 麦克风现场实时录音 -->
              <div v-else class="space-y-3 p-3.5 rounded-xl bg-slate-950/70 border border-slate-800">
                <!-- 录音控制栏 -->
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <span v-if="isRecording" class="h-2.5 w-2.5 rounded-full bg-red-500 animate-ping"></span>
                    <span v-else class="h-2.5 w-2.5 rounded-full" :class="recordedAudioUrl ? 'bg-emerald-400' : 'bg-slate-600'"></span>
                    <span class="text-xs font-mono font-medium" :class="isRecording ? 'text-red-400' : 'text-slate-400'">
                      {{ formatRecordTime(recordDuration) }}
                    </span>
                  </div>
                  
                  <div class="flex items-center gap-2">
                    <button
                      v-if="!isRecording"
                      type="button"
                      @click="startRecording"
                      class="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-white font-medium text-xs inline-flex items-center gap-1.5 shadow-md shadow-red-600/30 transition-all"
                    >
                      <Mic class="w-3.5 h-3.5" />
                      <span>{{ recordedAudioUrl ? '重新录制' : '开始现场录音' }}</span>
                    </button>
                    <button
                      v-else
                      type="button"
                      @click="stopRecording"
                      class="px-3 py-1.5 rounded-lg bg-slate-700 hover:bg-slate-600 text-white font-medium text-xs inline-flex items-center gap-1.5 shadow-md transition-all"
                    >
                      <Square class="w-3.5 h-3.5 fill-current text-red-400" />
                      <span>停止录音</span>
                    </button>
                  </div>
                </div>

                <!-- 实时跳动声波波形条 (录音时动态跳动) -->
                <div v-if="isRecording" class="h-9 flex items-center justify-center gap-1 bg-slate-900/60 rounded-lg px-2 border border-slate-800">
                  <div
                    v-for="(val, idx) in audioVisualizerData"
                    :key="idx"
                    class="w-1 bg-gradient-to-t from-red-500 to-amber-400 rounded-full transition-all duration-75"
                    :style="{ height: `${Math.max(4, val)}px` }"
                  ></div>
                </div>

                <!-- 录音完成后的回放试听 -->
                <div v-if="recordedAudioUrl && !isRecording" class="pt-2 border-t border-slate-800/80 space-y-1.5">
                  <div class="flex justify-between items-center text-[10px] text-slate-400">
                    <span>录音已就绪 (16kHz WAV)</span>
                    <span class="text-emerald-400 font-medium">已自动装载为转写源</span>
                  </div>
                  <audio controls :src="recordedAudioUrl" class="w-full h-8"></audio>
                </div>
              </div>
            </div>

            <button
              @click="submitExploreTranscribe"
              :disabled="isTranscribing || !selectedAudioFile"
              class="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold text-sm transition-all shadow-md shadow-indigo-600/20"
            >
              {{ isTranscribing ? '正在转写中...' : '开始转写测试' }}
            </button>
          </div>

          <!-- 右侧转写结果详情 -->
          <div class="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
            <h3 class="font-semibold text-white text-base flex justify-between items-center">
              <span>转写结果与对齐</span>
              <span v-if="exploreResult && exploreResult.result" class="text-xs text-slate-400 font-normal">
                耗时: {{ exploreResult.result.elapsed_ms }}ms · RTF: {{ exploreResult.result.rtf }} · 内存峰值: {{ exploreResult.result.memory_peak_mb }}MB
              </span>
            </h3>

            <div v-if="!exploreResult && !isTranscribing" class="h-64 flex flex-col items-center justify-center text-slate-500 border border-dashed border-slate-800 rounded-lg">
              <Headphones class="w-10 h-10 text-slate-600 mb-2" />
              <p class="text-xs">选择音频并点击开始转写测试</p>
            </div>

            <div v-if="isTranscribing" class="h-64 flex flex-col items-center justify-center text-indigo-400 space-y-3">
              <div class="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
              <p class="text-xs text-slate-400">正在独立 Worker 中执行推理采样...</p>
            </div>

            <div v-if="exploreResult" class="space-y-4">
              <!-- 音频播放 -->
              <div v-if="exploreResult.audio_file" class="bg-slate-800/40 p-3 rounded-lg border border-slate-800">
                <audio controls :src="exploreResult.audio_file" class="w-full h-8"></audio>
              </div>

              <!-- 失败显式错误卡片 -->
              <div v-if="exploreResult.result && !exploreResult.result.success" class="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 flex items-start gap-3">
                <AlertCircle class="w-5 h-5 mt-0.5 shrink-0 text-rose-400" />
                <div class="space-y-1">
                  <div class="font-semibold text-sm text-rose-200">转写执行失败</div>
                  <div class="text-xs font-mono text-rose-300/90 whitespace-pre-wrap leading-relaxed">{{ exploreResult.result.error }}</div>
                </div>
              </div>

              <!-- 成功时展示：指标卡片 -->
              <div v-if="exploreResult.result?.success && exploreResult.result.metrics" class="grid grid-cols-4 gap-2 text-center text-xs">
                <div class="bg-slate-800/60 p-2.5 rounded-lg border border-slate-700/50">
                  <div class="text-slate-400">CER / WER</div>
                  <div class="text-lg font-bold text-indigo-400">{{ (exploreResult.result.metrics.cer * 100).toFixed(1) }}%</div>
                </div>
                <div class="bg-slate-800/60 p-2.5 rounded-lg border border-slate-700/50">
                  <div class="text-slate-400">替换错误 (S)</div>
                  <div class="text-lg font-bold text-amber-400">{{ exploreResult.result.metrics.substitutions }}</div>
                </div>
                <div class="bg-slate-800/60 p-2.5 rounded-lg border border-slate-700/50">
                  <div class="text-slate-400">漏字 (D)</div>
                  <div class="text-lg font-bold text-red-400">{{ exploreResult.result.metrics.deletions }}</div>
                </div>
                <div class="bg-slate-800/60 p-2.5 rounded-lg border border-slate-700/50">
                  <div class="text-slate-400">幻觉多字 (I)</div>
                  <div class="text-lg font-bold text-purple-400">{{ exploreResult.result.metrics.insertions }}</div>
                </div>
              </div>

              <!-- 成功时展示：转写文本 -->
              <div v-if="exploreResult.result?.success" class="bg-slate-950 p-4 rounded-lg border border-slate-800">
                <div class="text-xs text-slate-400 mb-1">转写文本 (Hypothesis):</div>
                <p class="text-sm font-medium text-white leading-relaxed">{{ exploreResult.result.text || '(空输出)' }}</p>
              </div>

              <!-- 对齐高亮视图 -->
              <div v-if="exploreResult.result?.success && exploreResult.result.metrics?.alignments?.length" class="bg-slate-950 p-4 rounded-lg border border-slate-800">
                <div class="text-xs text-slate-400 mb-2">逐字编辑对齐:</div>
                <div class="flex flex-wrap gap-1 text-sm font-mono">
                  <span
                    v-for="(align, idx) in exploreResult.result.metrics.alignments"
                    :key="idx"
                    :class="[
                      'px-1.5 py-0.5 rounded text-xs',
                      align[0] === 'equal' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                      align[0] === 'sub' ? 'bg-amber-500/20 text-amber-300 line-through border border-amber-500/30' :
                      align[0] === 'del' ? 'bg-red-500/20 text-red-400 line-through' :
                      'bg-purple-500/20 text-purple-300 underline'
                    ]"
                    :title="align[0]"
                  >
                    {{ align[1] || align[2] }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 3. 模型评测工作区 -->
      <section v-if="activeTab === 'benchmark'" class="space-y-6">
        <div>
          <h2 class="text-xl font-bold text-white flex items-center gap-2">
            <Swords class="w-5 h-5 text-indigo-400" />
            <span>多模型串行对比评测</span>
          </h2>
          <p class="text-sm text-slate-400">按统一硬件条件串行运行模型测试，自动计算客观指标与多轮中位数</p>
        </div>

        <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-5">
          <!-- 维度选择 -->
          <div>
            <label class="block text-xs font-semibold text-slate-400 mb-2">选择测试集评测维度</label>
            <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2">
              <button
                v-for="dim in dimensions"
                :key="dim.id"
                @click="selectedDimension = dim.id"
                :class="[
                  'p-3 rounded-lg border text-left transition-all',
                  selectedDimension === dim.id
                    ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-md'
                    : 'bg-slate-800/40 border-slate-700/50 text-slate-400 hover:border-slate-600'
                ]"
              >
                <div class="font-semibold text-xs">{{ dim.name }}</div>
                <div class="text-[10px] text-slate-500 mt-1">{{ dim.item_count }} 条预设音频</div>
              </button>
            </div>
          </div>

          <!-- 模型多选 -->
          <div>
            <label class="block text-xs font-semibold text-slate-400 mb-2">勾选参与横评的模型</label>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
              <label
                v-for="m in models"
                :key="m.key"
                :class="[
                  'flex items-center space-x-2.5 p-2.5 rounded-lg border text-xs cursor-pointer transition-all',
                  selectedModelKeys.includes(m.key)
                    ? 'bg-indigo-500/10 border-indigo-500/50 text-indigo-300'
                    : 'bg-slate-800/30 border-slate-800 text-slate-400 hover:border-slate-700'
                ]"
              >
                <input
                  type="checkbox"
                  :value="m.key"
                  v-model="selectedModelKeys"
                  class="rounded border-slate-700 text-indigo-600 focus:ring-indigo-500"
                />
                <span class="truncate">{{ m.name }}</span>
              </label>
            </div>
          </div>

          <!-- 重复次数与模式 -->
          <div class="flex flex-wrap gap-6 items-center pt-2">
            <div>
              <span class="text-xs font-semibold text-slate-400 mr-2">重复次数:</span>
              <div class="inline-flex rounded-lg border border-slate-700 bg-slate-800 p-0.5 text-xs">
                <button
                  v-for="r in [1, 2, 3, 5]"
                  :key="r"
                  @click="selectedRepeats = r"
                  :class="[
                    'px-2.5 py-1 rounded-md font-medium transition-all',
                    selectedRepeats === r ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                  ]"
                >
                  {{ r }}次
                </button>
              </div>
            </div>

            <div>
              <span class="text-xs font-semibold text-slate-400 mr-2">推理模式:</span>
              <div class="inline-flex rounded-lg border border-slate-700 bg-slate-800 p-0.5 text-xs">
                <button
                  @click="benchmarkMode = 'offline'"
                  :class="[
                    'px-2.5 py-1 rounded-md font-medium transition-all',
                    benchmarkMode === 'offline' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                  ]"
                >
                  离线转写 (RTF)
                </button>
                <button
                  @click="benchmarkMode = 'streaming'"
                  :class="[
                    'px-2.5 py-1 rounded-md font-medium transition-all',
                    benchmarkMode === 'streaming' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                  ]"
                >
                  实时流式 (TTFB)
                </button>
              </div>
            </div>

            <button
              @click="startBenchmarkJob"
              :disabled="selectedModelKeys.length === 0 || isRunningJob"
              class="ml-auto px-5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-bold transition-all shadow-md shadow-indigo-600/30 flex items-center gap-1.5"
            >
              <Play class="w-3.5 h-3.5 fill-current" />
              <span>{{ isRunningJob ? '评测批次运行中...' : '启动批次横评' }}</span>
            </button>
          </div>
        </div>

        <!-- 实时执行进度 -->
        <div v-if="activeJob" class="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div class="flex justify-between items-center text-sm">
            <span class="font-bold text-white flex items-center gap-2">
              <span :class="['h-2 w-2 rounded-full', activeJob.status === 'running' ? 'bg-indigo-400 animate-pulse' : 'bg-emerald-400']"></span>
              批次进度: {{ activeJob.completed_tasks }} / {{ activeJob.total_tasks }} 项
              <span class="text-xs text-slate-400 font-mono font-normal">({{ activeJob.job_id }})</span>
            </span>
            <div class="flex items-center gap-3">
              <span class="text-xs text-slate-400 font-mono">状态: {{ activeJob.status }}</span>
              <button
                v-if="activeJob.status === 'running'"
                @click="stopActiveJob"
                class="px-2.5 py-1 rounded-md bg-rose-500/20 hover:bg-rose-500/30 border border-rose-500/40 text-rose-300 text-xs font-medium transition-all"
              >
                停止评测
              </button>
              <button
                v-else
                @click="viewJobDetail(activeJob)"
                class="px-2.5 py-1 rounded-md bg-indigo-500/20 hover:bg-indigo-500/30 border border-indigo-500/40 text-indigo-300 text-xs font-medium transition-all flex items-center gap-1"
              >
                <BarChart3 class="w-3 h-3" />
                <span>查看分析</span>
              </button>
            </div>
          </div>

          <div class="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
            <div
              class="bg-gradient-to-r from-indigo-500 to-sky-400 h-full transition-all duration-300"
              :style="{ width: `${(activeJob.completed_tasks / (activeJob.total_tasks || 1)) * 100}%` }"
            ></div>
          </div>
        </div>
      </section>

      <!-- 4. 结果分析与图表 -->
      <section v-if="activeTab === 'analysis'" class="space-y-6">
        <!-- 顶部标题与批次上下文切换栏 -->
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg">
          <div class="space-y-1">
            <h2 class="text-xl font-bold text-white flex items-center gap-2">
              <BarChart3 class="w-5 h-5 text-indigo-400" />
              <span>评测结果多维深度分析</span>
            </h2>
            <p class="text-xs text-slate-400">
              从准确率天梯、实时率倍数、硬件开销及字级 Diff 等多维度横向切片对比
            </p>
          </div>

          <!-- 历史批次快速切换选择器 -->
          <div v-if="jobHistory.length > 0" class="flex items-center gap-2.5">
            <span class="text-xs text-slate-400 shrink-0 font-medium">当前批次:</span>
            <select
              :value="activeJob?.job_id"
              @change="switchAnalysisJob(($event.target as HTMLSelectElement).value)"
              class="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono shadow-inner"
            >
              <option v-for="j in jobHistory" :key="j.job_id" :value="j.job_id">
                {{ j.job_id }} ({{ j.dimension }} · {{ j.completed_tasks }}/{{ j.total_tasks }} · {{ j.status }})
              </option>
            </select>
          </div>
        </div>

        <div v-if="activeJob && activeJob.tasks.length > 0" class="space-y-6">
          <!-- 批次基础指标概览卡片 -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div class="bg-slate-900/80 border border-slate-800/80 rounded-xl p-4">
              <span class="text-[11px] text-slate-400">评测维度</span>
              <div class="text-base font-bold text-indigo-300 mt-1 truncate">{{ activeJob.dimension }}</div>
              <div class="text-[10px] text-slate-500 mt-0.5">模式: {{ activeJob.mode === 'streaming' ? '实时流式' : '离线转写' }}</div>
            </div>
            <div class="bg-slate-900/80 border border-slate-800/80 rounded-xl p-4">
              <span class="text-[11px] text-slate-400">参评模型数</span>
              <div class="text-base font-bold text-white mt-1">{{ aggregatedModelStats.length }} 款模型</div>
              <div class="text-[10px] text-slate-500 mt-0.5">多模型同台竞技</div>
            </div>
            <div class="bg-slate-900/80 border border-slate-800/80 rounded-xl p-4">
              <span class="text-[11px] text-slate-400">测试任务量</span>
              <div class="text-base font-bold text-white mt-1">{{ activeJob.completed_tasks }} / {{ activeJob.total_tasks }} 项</div>
              <div class="text-[10px] text-slate-500 mt-0.5 font-mono">状态: {{ activeJob.status }}</div>
            </div>
            <div class="bg-slate-900/80 border border-slate-800/80 rounded-xl p-4">
              <span class="text-[11px] text-slate-400">最佳准确模型</span>
              <div class="text-base font-bold text-emerald-400 mt-1 truncate">
                {{ aggregatedModelStats[0]?.model_key || '-' }}
              </div>
              <div class="text-[10px] text-slate-500 mt-0.5 font-mono">
                平均 CER: {{ aggregatedModelStats[0] ? `${aggregatedModelStats[0].avg_cer.toFixed(1)}%` : '-' }}
              </div>
            </div>
          </div>

          <!-- 多维度分析导航 Tabs 与排序器 -->
          <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
            <div class="flex flex-wrap gap-2">
              <button
                @click="analysisSubTab = 'leaderboard'"
                :class="[
                  'px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all',
                  analysisSubTab === 'leaderboard'
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                    : 'bg-slate-800/60 text-slate-400 hover:text-white'
                ]"
              >
                <Trophy class="w-3.5 h-3.5" />
                <span>综合天梯榜</span>
              </button>
              <button
                @click="analysisSubTab = 'charts'"
                :class="[
                  'px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all',
                  analysisSubTab === 'charts'
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                    : 'bg-slate-800/60 text-slate-400 hover:text-white'
                ]"
              >
                <Activity class="w-3.5 h-3.5" />
                <span>指标横向透视</span>
              </button>
              <button
                @click="analysisSubTab = 'diff'"
                :class="[
                  'px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all',
                  analysisSubTab === 'diff'
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                    : 'bg-slate-800/60 text-slate-400 hover:text-white'
                ]"
              >
                <FileText class="w-3.5 h-3.5" />
                <span>文本 Diff 对齐</span>
              </button>
              <button
                @click="analysisSubTab = 'errors'"
                :class="[
                  'px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all',
                  analysisSubTab === 'errors'
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                    : 'bg-slate-800/60 text-slate-400 hover:text-white'
                ]"
              >
                <Layers class="w-3.5 h-3.5" />
                <span>错误类型分解 (S/D/I)</span>
              </button>
              <button
                @click="analysisSubTab = 'raw'"
                :class="[
                  'px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all',
                  analysisSubTab === 'raw'
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                    : 'bg-slate-800/60 text-slate-400 hover:text-white'
                ]"
              >
                <ClipboardList class="w-3.5 h-3.5" />
                <span>原始流水账</span>
              </button>
            </div>

            <!-- 排序切换（在 Leaderboard 或 Charts 下显示） -->
            <div v-if="analysisSubTab === 'leaderboard' || analysisSubTab === 'charts'" class="flex items-center gap-2 text-xs">
              <span class="text-slate-400 flex items-center gap-1 text-[11px]">
                <ArrowUpDown class="w-3 h-3" />
                <span>排序依据:</span>
              </span>
              <div class="inline-flex rounded-lg border border-slate-700 bg-slate-800/80 p-0.5 text-[11px]">
                <button
                  @click="analysisSortBy = 'cer'"
                  :class="['px-2.5 py-1 rounded-md transition-all', analysisSortBy === 'cer' ? 'bg-indigo-600 text-white font-bold' : 'text-slate-400 hover:text-white']"
                >
                  准确率 (CER 最低)
                </button>
                <button
                  @click="analysisSortBy = 'rtf'"
                  :class="['px-2.5 py-1 rounded-md transition-all', analysisSortBy === 'rtf' ? 'bg-indigo-600 text-white font-bold' : 'text-slate-400 hover:text-white']"
                >
                  速度 (RTF 最快)
                </button>
                <button
                  @click="analysisSortBy = 'memory'"
                  :class="['px-2.5 py-1 rounded-md transition-all', analysisSortBy === 'memory' ? 'bg-indigo-600 text-white font-bold' : 'text-slate-400 hover:text-white']"
                >
                  低显存 (RAM 最小)
                </button>
              </div>
            </div>
          </div>

          <!-- 维度 1：综合天梯榜 (Leaderboard) -->
          <div v-if="analysisSubTab === 'leaderboard'" class="space-y-4">
            <div class="overflow-x-auto bg-slate-900 border border-slate-800 rounded-2xl shadow-xl">
              <table class="w-full text-left text-xs">
                <thead class="bg-slate-800/60 text-slate-400 border-b border-slate-800 font-sans">
                  <tr>
                    <th class="p-4 w-12 text-center whitespace-nowrap">排名</th>
                    <th class="p-4 min-w-[170px]">模型及定位</th>
                    <th class="p-4 min-w-[210px]">选型关键特性 (流式 / 语种 / 扩展)</th>
                    <th class="p-4 min-w-[130px] whitespace-nowrap">平均 CER (字错误率)</th>
                    <th class="p-4 min-w-[160px] whitespace-nowrap">推理实时率 (RTF)</th>
                    <th class="p-4 min-w-[100px] whitespace-nowrap">平均耗时</th>
                    <th class="p-4 min-w-[100px] whitespace-nowrap">内存峰值 (RAM)</th>
                    <th class="p-4 w-16 text-center whitespace-nowrap">稳定性</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-800/60 font-sans">
                  <tr
                    v-for="(stat, idx) in aggregatedModelStats"
                    :key="stat.model_key"
                    class="hover:bg-slate-800/40 transition-colors"
                  >
                    <!-- 排名勋章 -->
                    <td class="p-4 text-center whitespace-nowrap">
                      <span v-if="idx === 0" class="text-base" title="金牌 No.1">🥇</span>
                      <span v-else-if="idx === 1" class="text-base" title="银牌 No.2">🥈</span>
                      <span v-else-if="idx === 2" class="text-base" title="铜牌 No.3">🥉</span>
                      <span v-else class="text-xs font-mono font-bold text-slate-500">#{{ idx + 1 }}</span>
                    </td>

                    <!-- 模型名称与特性标签 -->
                    <td class="p-4">
                      <div class="flex items-center gap-2">
                        <span class="font-bold text-sm text-white">{{ stat.model_key }}</span>
                        <span :class="['text-[10px] px-2 py-0.5 rounded-full border font-medium whitespace-nowrap', stat.badge.color]">
                          {{ stat.badge.title }}
                        </span>
                      </div>
                      <div class="text-[11px] text-slate-400 mt-0.5 truncate max-w-xs">{{ stat.model_name }}</div>
                    </td>

                    <!-- 选型关键特性（流式/语种/扩展功能） -->
                    <td class="p-4">
                      <div class="flex flex-wrap items-center gap-1.5 max-w-xs">
                        <!-- 流式支持 -->
                        <span
                          :class="[
                            'text-[10px] px-2 py-0.5 rounded-full border font-medium inline-flex items-center gap-1 whitespace-nowrap',
                            stat.meta?.supports_streaming
                              ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300 font-semibold shadow-xs'
                              : 'bg-slate-800/80 border-slate-700/60 text-slate-400'
                          ]"
                        >
                          <Zap v-if="stat.meta?.supports_streaming" class="w-2.5 h-2.5 text-emerald-400" />
                          {{ stat.meta?.supports_streaming ? '支持流式' : '仅离线' }}
                        </span>

                        <!-- 语言覆盖 -->
                        <span
                          class="text-[10px] px-2 py-0.5 rounded-full bg-sky-500/10 border border-sky-500/30 text-sky-300 font-mono whitespace-nowrap"
                          :title="`支持语种: ${(stat.meta?.languages || []).join(', ')}`"
                        >
                          {{ (stat.meta?.languages || []).slice(0, 3).join('/') }}{{ (stat.meta?.languages || []).length > 3 ? '等多语' : '' }}
                        </span>

                        <!-- 情感/声音事件识别 -->
                        <span
                          v-if="stat.meta?.supports_emotion"
                          class="text-[10px] px-2 py-0.5 rounded-full bg-fuchsia-500/15 border border-fuchsia-500/30 text-fuchsia-300 font-medium whitespace-nowrap"
                          title="支持情感与语气/笑声/掌声等声音事件识别"
                        >
                          情感识别
                        </span>

                        <!-- 时间戳对齐 -->
                        <span
                          v-if="stat.meta?.supports_timestamps"
                          class="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 whitespace-nowrap"
                          title="支持高精度逐词/逐句时间戳输出"
                        >
                          时间戳
                        </span>

                        <!-- Mac 部署后端 -->
                        <span
                          v-if="stat.meta?.mac_backend"
                          class="text-[10px] px-2 py-0.5 rounded-full bg-slate-950/80 border border-slate-800 text-slate-400 truncate max-w-[120px] whitespace-nowrap"
                          :title="stat.meta.mac_backend"
                        >
                          {{ stat.meta.mac_backend.split('/')[0].trim() }}
                        </span>
                      </div>
                    </td>

                    <!-- 平均 CER -->
                    <td class="p-4 whitespace-nowrap">
                      <div class="flex items-center gap-2">
                        <span class="text-sm font-extrabold font-mono text-white">{{ stat.avg_cer.toFixed(1) }}%</span>
                        <span :class="['text-[10px] px-1.5 py-0.5 rounded border whitespace-nowrap', stat.cer_level.color]">
                          {{ stat.cer_level.label }}
                        </span>
                      </div>
                      <div class="text-[10px] text-slate-500 mt-1 font-mono">
                        单句区间: {{ stat.min_cer.toFixed(1) }}% ~ {{ stat.max_cer.toFixed(1) }}%
                      </div>
                    </td>

                    <!-- 推理实时率 (RTF) - 强制单行不折行 -->
                    <td class="p-4 whitespace-nowrap">
                      <div class="flex items-center gap-1.5 whitespace-nowrap">
                        <span class="text-sm font-bold font-mono text-white">{{ stat.avg_rtf.toFixed(3) }}</span>
                        <span class="text-[11px] text-slate-400 font-sans whitespace-nowrap">
                          ({{ stat.avg_rtf < 1.0 ? `${(1.0 / (stat.avg_rtf || 0.001)).toFixed(1)}x 极速` : '慢于实时' }})
                        </span>
                      </div>
                      <div :class="['text-[10px] mt-1 font-medium font-sans whitespace-nowrap inline-block', stat.rtf_level.color]">
                        {{ stat.rtf_level.label }}
                      </div>
                    </td>

                    <!-- 平均耗时 - 紧凑双行堆叠 -->
                    <td class="p-4 font-mono whitespace-nowrap">
                      <div class="flex flex-col">
                        <span class="text-xs font-bold text-slate-200">{{ (stat.avg_elapsed_ms / 1000).toFixed(2) }}s</span>
                        <span class="text-[10px] text-slate-500 font-normal mt-0.5">{{ Math.round(stat.avg_elapsed_ms).toLocaleString() }} ms</span>
                      </div>
                    </td>

                    <!-- 内存峰值 - 紧凑双行堆叠 -->
                    <td class="p-4 font-mono whitespace-nowrap">
                      <div class="flex flex-col">
                        <span class="text-xs font-bold text-slate-200">{{ stat.peak_memory_mb.toFixed(1) }} MB</span>
                        <span class="text-[10px] text-slate-500 font-normal mt-0.5">{{ (stat.peak_memory_mb / 1024).toFixed(2) }} GB</span>
                      </div>
                    </td>

                    <!-- 稳定性 -->
                    <td class="p-4 text-center font-mono whitespace-nowrap">
                      <span class="text-emerald-400 font-semibold">{{ stat.success_count }}/{{ stat.task_count }}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- 维度 2：指标横向透视 (Charts) -->
          <div v-if="analysisSubTab === 'charts'" class="space-y-6">
            <!-- 精度 CER 条形对比 -->
            <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-lg">
              <div class="flex justify-between items-center">
                <h3 class="text-sm font-bold text-white flex items-center gap-2">
                  <Award class="w-4 h-4 text-emerald-400" />
                  <span>字错误率 (CER) 横向对比 - 越低越精准</span>
                </h3>
                <span class="text-[11px] text-slate-400">0% 为逐字绝对匹配</span>
              </div>

              <div class="space-y-3 pt-2">
                <div v-for="stat in aggregatedModelStats" :key="stat.model_key" class="space-y-1">
                  <div class="flex justify-between items-center text-xs">
                    <span class="font-medium text-slate-200 font-mono">{{ stat.model_key }}</span>
                    <span class="font-bold font-mono text-emerald-400">{{ stat.avg_cer.toFixed(1) }}%</span>
                  </div>
                  <div class="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden flex">
                    <div
                      :class="[
                        'h-full rounded-full transition-all duration-500',
                        stat.avg_cer <= 2 ? 'bg-emerald-400' : stat.avg_cer <= 5 ? 'bg-sky-400' : stat.avg_cer <= 15 ? 'bg-amber-400' : 'bg-rose-500'
                      ]"
                      :style="{ width: `${Math.min(Math.max(stat.avg_cer * 2, 2), 100)}%` }"
                    ></div>
                  </div>
                </div>
              </div>
            </div>

            <!-- RTF 实时率对比（带 1.0x 基准） -->
            <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-lg">
              <div class="flex justify-between items-center">
                <h3 class="text-sm font-bold text-white flex items-center gap-2">
                  <Zap class="w-4 h-4 text-amber-400" />
                  <span>实时率 (RTF) 对比 - 越低越快 (低于 1.0 为实时在线推理能力)</span>
                </h3>
                <span class="text-[11px] text-amber-400/90 font-mono font-medium">基准参考线: 1.0x 实时</span>
              </div>

              <div class="space-y-3 pt-2">
                <div v-for="stat in aggregatedModelStats" :key="stat.model_key" class="space-y-1">
                  <div class="flex justify-between items-center text-xs">
                    <span class="font-medium text-slate-200 font-mono">{{ stat.model_key }}</span>
                    <span class="font-bold font-mono text-amber-300">
                      RTF: {{ stat.avg_rtf.toFixed(3) }}
                      <span class="text-[10px] text-slate-400 font-normal font-sans">({{ (stat.avg_elapsed_ms / 1000).toFixed(1) }}s)</span>
                    </span>
                  </div>
                  <div class="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden flex">
                    <div
                      :class="[
                        'h-full rounded-full transition-all duration-500',
                        stat.avg_rtf <= 1.0 ? 'bg-gradient-to-r from-emerald-500 to-sky-400' : 'bg-gradient-to-r from-amber-500 to-rose-500'
                      ]"
                      :style="{ width: `${Math.min(stat.avg_rtf * 15, 100)}%` }"
                    ></div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 内存开销对比 -->
            <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-lg">
              <div class="flex justify-between items-center">
                <h3 class="text-sm font-bold text-white flex items-center gap-2">
                  <HardDrive class="w-4 h-4 text-sky-400" />
                  <span>物理内存峰值占用 (RAM Peak) - 越小端侧越轻量</span>
                </h3>
                <span class="text-[11px] text-slate-400">MB / 显存开销</span>
              </div>

              <div class="space-y-3 pt-2">
                <div v-for="stat in aggregatedModelStats" :key="stat.model_key" class="space-y-1">
                  <div class="flex justify-between items-center text-xs">
                    <span class="font-medium text-slate-200 font-mono">{{ stat.model_key }}</span>
                    <span class="font-bold font-mono text-sky-300">{{ stat.peak_memory_mb.toFixed(1) }} MB</span>
                  </div>
                  <div class="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden flex">
                    <div
                      class="h-full bg-gradient-to-r from-sky-500 to-indigo-500 rounded-full transition-all duration-500"
                      :style="{ width: `${Math.min((stat.peak_memory_mb / 4500) * 100, 100)}%` }"
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 维度 3：文本 Diff 逐字对齐下钻 (Diff) -->
          <div v-if="analysisSubTab === 'diff'" class="space-y-5">
            <!-- 音频样本选择器 -->
            <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-md">
              <div class="flex items-center gap-2">
                <FileText class="w-4 h-4 text-indigo-400" />
                <span class="text-xs font-bold text-white">选择比对音频样本:</span>
              </div>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="audio in analysisAudioList"
                  :key="audio"
                  @click="selectedAnalysisAudio = audio"
                  :class="[
                    'px-3 py-1.5 rounded-lg text-xs font-mono transition-all',
                    (selectedAnalysisAudio || analysisAudioList[0]) === audio
                      ? 'bg-indigo-600 text-white font-bold shadow-md shadow-indigo-600/30'
                      : 'bg-slate-800 text-slate-400 hover:text-white border border-slate-700/60'
                  ]"
                >
                  {{ audio }}
                </button>
              </div>
            </div>

            <!-- 标准参考真值展示 -->
            <div class="bg-slate-950 border border-indigo-500/30 rounded-2xl p-5 space-y-2 shadow-lg">
              <div class="flex items-center justify-between">
                <span class="text-xs font-bold text-indigo-400 flex items-center gap-1.5">
                  <CheckCircle2 class="w-4 h-4" />
                  <span>标准参考真值 (Ground Truth):</span>
                </span>
                <span class="text-[11px] text-slate-500 font-mono">{{ (selectedAnalysisAudio || analysisAudioList[0]) }}</span>
              </div>
              <div class="p-3 bg-slate-900/90 rounded-xl border border-slate-800 text-sm font-sans font-medium text-slate-100 select-all">
                {{ currentDiffTasks[0]?.reference_text || '暂无标注真值' }}
              </div>
            </div>

            <!-- 各模型识别文本与差异卡片 -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div
                v-for="task in currentDiffTasks"
                :key="task.task_id"
                class="bg-slate-900 border border-slate-800 rounded-2xl p-4 space-y-3 hover:border-slate-700 transition-all shadow-md"
              >
                <div class="flex justify-between items-center">
                  <div class="flex items-center gap-2">
                    <span class="font-bold text-xs text-white">{{ task.model_key }}</span>
                    <span
                      v-if="task.result?.metrics?.cer === 0"
                      class="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-medium"
                    >
                      100% 完美匹配 ✨
                    </span>
                    <span
                      v-else
                      class="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 font-mono"
                    >
                      CER: {{ ((task.result?.metrics?.cer || 0) * 100).toFixed(1) }}%
                    </span>
                  </div>
                  <div class="text-[11px] text-slate-500 font-mono">
                    耗时: {{ task.result?.elapsed_ms }}ms · RTF: {{ task.result?.rtf?.toFixed(2) }}
                  </div>
                </div>

                <!-- 识别结果文本 -->
                <div class="p-3 bg-slate-950/70 rounded-xl border border-slate-800/80 text-xs font-sans text-slate-200 leading-relaxed min-h-[50px]">
                  {{ task.result?.text || '（空转写结果）' }}
                </div>

                <!-- 差异标记详情 -->
                <div v-if="task.result?.metrics?.alignments" class="text-[11px] text-slate-400 space-y-1">
                  <span class="text-slate-500">字级差异拆解:</span>
                  <div class="flex flex-wrap gap-1.5 pt-1">
                    <template v-for="(align, i) in task.result.metrics.alignments" :key="i">
                      <span v-if="align[0] === 'sub'" class="px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 text-[10px]" :title="`真值: ${align[1]} -> 误识: ${align[2]}`">
                        替换: {{ align[1] }}→{{ align[2] }}
                      </span>
                      <span v-else-if="align[0] === 'del'" class="px-1.5 py-0.5 rounded bg-red-500/20 text-red-300 line-through border border-red-500/40 text-[10px]" :title="`漏读: ${align[1]}`">
                        漏读: {{ align[1] }}
                      </span>
                      <span v-else-if="align[0] === 'ins'" class="px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/40 text-[10px]" :title="`多出: ${align[2]}`">
                        多字: {{ align[2] }}
                      </span>
                    </template>
                    <span v-if="task.result.metrics.cer === 0" class="text-emerald-400 text-[11px]">
                      无任何错漏，全字精准对齐。
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 维度 4：错误类型分解 (Errors) -->
          <div v-if="analysisSubTab === 'errors'" class="space-y-4">
            <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-2 shadow-lg">
              <h3 class="text-sm font-bold text-white flex items-center gap-2">
                <Layers class="w-4 h-4 text-purple-400" />
                <span>ASR 错因归因体系 (Substitution / Deletion / Insertion)</span>
              </h3>
              <p class="text-xs text-slate-400">
                <span class="text-amber-400 font-medium">S 替换错误</span> (拼音相近/同音异字) ·
                <span class="text-red-400 font-medium">D 删除错误</span> (语速快吞音/漏词) ·
                <span class="text-purple-400 font-medium">I 插入错误</span> (噪音杂音幻觉多字)
              </p>
            </div>

            <div class="overflow-x-auto bg-slate-900 border border-slate-800 rounded-2xl shadow-xl">
              <table class="w-full text-left text-xs">
                <thead class="bg-slate-800/60 text-slate-400 border-b border-slate-800 font-sans">
                  <tr>
                    <th class="p-4">模型</th>
                    <th class="p-4 text-amber-400">替换错误 (S)</th>
                    <th class="p-4 text-red-400">删除错误 (D)</th>
                    <th class="p-4 text-purple-400">插入错误 (I)</th>
                    <th class="p-4">错误总计</th>
                    <th class="p-4 w-64">错因偏向分布</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-800/60 font-sans">
                  <tr v-for="stat in aggregatedModelStats" :key="stat.model_key" class="hover:bg-slate-800/40">
                    <td class="p-4 font-mono font-bold text-white">{{ stat.model_key }}</td>
                    <td class="p-4 font-mono text-amber-300 font-semibold">{{ stat.total_sub }} 字</td>
                    <td class="p-4 font-mono text-red-300 font-semibold">{{ stat.total_del }} 字</td>
                    <td class="p-4 font-mono text-purple-300 font-semibold">{{ stat.total_ins }} 字</td>
                    <td class="p-4 font-mono text-slate-200 font-bold">{{ stat.total_errors }} 字</td>
                    <td class="p-4">
                      <div v-if="stat.total_errors > 0" class="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden flex">
                        <div
                          class="bg-amber-400 h-full"
                          :style="{ width: `${(stat.total_sub / stat.total_errors) * 100}%` }"
                          title="替换占比"
                        ></div>
                        <div
                          class="bg-red-400 h-full"
                          :style="{ width: `${(stat.total_del / stat.total_errors) * 100}%` }"
                          title="删除占比"
                        ></div>
                        <div
                          class="bg-purple-400 h-full"
                          :style="{ width: `${(stat.total_ins / stat.total_errors) * 100}%` }"
                          title="插入占比"
                        ></div>
                      </div>
                      <span v-else class="text-[11px] text-emerald-400 font-medium">无任何错误 💯</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- 维度 5：原始流水账 (Raw) -->
          <div v-if="analysisSubTab === 'raw'" class="space-y-4">
            <div class="overflow-x-auto bg-slate-900 border border-slate-800 rounded-xl">
              <table class="w-full text-left text-xs">
                <thead class="bg-slate-800/50 text-slate-400 border-b border-slate-800 uppercase font-mono">
                  <tr>
                    <th class="p-3.5">模型</th>
                    <th class="p-3.5">音频</th>
                    <th class="p-3.5">状态</th>
                    <th class="p-3.5">CER</th>
                    <th class="p-3.5">耗时 (ms)</th>
                    <th class="p-3.5">RTF</th>
                    <th class="p-3.5">内存峰值 (MB)</th>
                    <th class="p-3.5">S / D / I 错误分解</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-800/60 font-mono">
                  <tr v-for="t in activeJob.tasks" :key="t.task_id" class="hover:bg-slate-800/30">
                    <td class="p-3.5 font-sans font-medium text-white">{{ t.model_key }}</td>
                    <td class="p-3.5 text-slate-400 max-w-xs truncate">{{ t.audio_file.split('/').pop() }}</td>
                    <td class="p-3.5">
                      <span :class="t.status === 'success' ? 'text-emerald-400' : t.status === 'running' ? 'text-indigo-400 animate-pulse' : 'text-slate-500'">
                        {{ t.status }}
                      </span>
                    </td>
                    <td class="p-3.5 font-bold text-indigo-300">
                      {{ t.result?.metrics ? `${(t.result.metrics.cer * 100).toFixed(1)}%` : '-' }}
                    </td>
                    <td class="p-3.5 text-slate-300">{{ t.result?.elapsed_ms || '-' }}</td>
                    <td class="p-3.5 text-slate-300">{{ t.result?.rtf || '-' }}</td>
                    <td class="p-3.5 text-slate-300">{{ t.result?.memory_peak_mb || '-' }}</td>
                    <td class="p-3.5 text-slate-400">
                      <span v-if="t.result?.metrics">
                        <span class="text-amber-400">S:{{ t.result.metrics.substitutions }}</span> ·
                        <span class="text-red-400">D:{{ t.result.metrics.deletions }}</span> ·
                        <span class="text-purple-400">I:{{ t.result.metrics.insertions }}</span>
                      </span>
                      <span v-else>-</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- 空数据提示 -->
        <div v-else class="h-64 flex flex-col items-center justify-center text-slate-500 bg-slate-900 border border-slate-800 rounded-xl">
          <ClipboardList class="w-10 h-10 text-slate-600 mb-2" />
          <p class="text-xs">暂无活动批次数据，请先到「模型评测」中发起批次</p>
        </div>
      </section>

      <!-- 5. 转写对比工作区 -->
      <section v-if="activeTab === 'comparison'" class="space-y-6">
        <div>
          <h2 class="text-xl font-bold text-white flex items-center gap-2">
            <GitCompare class="w-5 h-5 text-indigo-400" />
            <span>同音频 A/B 转写对比</span>
          </h2>
          <p class="text-sm text-slate-400">选择两个不同模型的转写结果并排比对，高亮字词差异</p>
        </div>

        <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 text-center text-slate-500 text-xs py-12">
          支持从历史批次或能力探索中拉取双模型同一音频转写，进行字级 Diff 高亮对比与人工标注。
        </div>
      </section>

      <!-- 6. 历史管理工作区 -->
      <section v-if="activeTab === 'history'" class="space-y-6">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 class="text-xl font-bold text-white flex items-center gap-2">
              <History class="w-5 h-5 text-indigo-400" />
              <span>评测历史与回收站</span>
            </h2>
            <p class="text-sm text-slate-400">管理历史批次快照，支持状态自愈追踪与报告下钻查看</p>
          </div>
          <button
            @click="loadHistory"
            :disabled="isLoadingHistory"
            class="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-xs font-medium transition-all shadow-sm self-start sm:self-auto"
          >
            <RefreshCw :class="['w-3.5 h-3.5', isLoadingHistory ? 'animate-spin text-indigo-400' : '']" />
            <span>刷新列表</span>
          </button>
        </div>

        <div v-if="jobHistory.length > 0" class="overflow-x-auto bg-slate-900 border border-slate-800 rounded-xl">
          <table class="w-full text-left text-xs">
            <thead class="bg-slate-800/50 text-slate-400 border-b border-slate-800">
              <tr>
                <th class="p-3.5">批次 ID</th>
                <th class="p-3.5">评测维度</th>
                <th class="p-3.5">参与模型</th>
                <th class="p-3.5">任务数</th>
                <th class="p-3.5">状态</th>
                <th class="p-3.5">创建时间</th>
                <th class="p-3.5 text-right">操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-800/60 font-mono">
              <tr v-for="job in jobHistory" :key="job.job_id" class="hover:bg-slate-800/30">
                <td class="p-3.5 text-indigo-400 font-mono text-[11px]">{{ job.job_id }}</td>
                <td class="p-3.5 text-slate-300 font-sans">{{ job.dimension }}</td>
                <td class="p-3.5 text-slate-400 text-[11px] max-w-xs truncate font-sans" :title="job.model_keys.join(', ')">{{ job.model_keys.join(', ') }}</td>
                <td class="p-3.5 text-slate-300 font-mono">{{ job.completed_tasks }}/{{ job.total_tasks }}</td>
                <td class="p-3.5 font-sans">
                  <span v-if="job.status === 'running'" class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 text-[11px] font-medium">
                    <span class="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse"></span>
                    运行中
                  </span>
                  <span v-else-if="job.status === 'completed'" class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[11px] font-medium">
                    <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                    已完成
                  </span>
                  <span v-else-if="job.status === 'interrupted'" class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-[11px] font-medium" title="服务重启中断">
                    <span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
                    已中断
                  </span>
                  <span v-else-if="job.status === 'stopped'" class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-400 text-[11px] font-medium">
                    <span class="w-1.5 h-1.5 rounded-full bg-slate-400"></span>
                    已停止
                  </span>
                  <span v-else-if="job.status === 'failed'" class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-rose-500/10 border border-rose-500/30 text-rose-400 text-[11px] font-medium">
                    <span class="w-1.5 h-1.5 rounded-full bg-rose-400"></span>
                    失败
                  </span>
                  <span v-else class="text-xs text-slate-400">{{ job.status }}</span>
                </td>
                <td class="p-3.5 text-slate-500 font-mono text-[11px]">{{ new Date(job.created_at * 1000).toLocaleString() }}</td>
                <td class="p-3.5 text-right font-sans">
                  <div class="inline-flex items-center gap-2">
                    <button
                      @click="viewJobDetail(job)"
                      class="text-indigo-400 hover:text-indigo-300 text-xs inline-flex items-center gap-1 px-2 py-1 rounded bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/20 transition-all"
                    >
                      <BarChart3 class="w-3.5 h-3.5" />
                      <span>查看报告</span>
                    </button>
                    <button
                      @click="deleteJob(job.job_id)"
                      class="text-red-400 hover:text-red-300 text-xs inline-flex items-center gap-1 px-2 py-1 rounded hover:bg-red-500/10 transition-all"
                    >
                      <Trash2 class="w-3.5 h-3.5" />
                      <span>移入回收站</span>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="h-48 flex flex-col items-center justify-center text-slate-500 bg-slate-900 border border-slate-800 rounded-xl text-xs">
          暂无历史批次
        </div>
      </section>

    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import {
  Mic,
  Square,
  Upload,
  Compass,
  FlaskConical,
  Swords,
  BarChart3,
  GitCompare,
  History,
  Headphones,
  ClipboardList,
  Play,
  Trash2,
  AlertCircle,
  RefreshCw,
  Trophy,
  Award,
  Zap,
  HardDrive,
  Layers,
  CheckCircle2,
  FileText,
  ArrowUpDown,
  Activity,
} from 'lucide-vue-next'

interface SystemInfo {
  machine: string
  is_apple_silicon: boolean
  memory_total_gb: number
  memory_available_gb: number
}

interface ModelItem {
  key: string
  name: string
  parameters: string
  download_size: string
  license: string
  languages: string[]
  supports_streaming: boolean
  supports_timestamps?: boolean
  supports_emotion?: boolean
  recommended_device?: string
  repo_id?: string
  mac_backend: string
  is_available: boolean
  venv_name: string
}

interface DimensionItem {
  id: string
  name: string
  description: string
  item_count: number
}

const tabs = [
  { id: 'scenario', name: '场景选型', icon: Compass },
  { id: 'explore', name: '能力探索', icon: FlaskConical },
  { id: 'benchmark', name: '模型评测', icon: Swords },
  { id: 'analysis', name: '结果分析', icon: BarChart3 },
  { id: 'comparison', name: '转写对比', icon: GitCompare },
  { id: 'history', name: '历史管理', icon: History },
]

const activeTab = ref('scenario')
const systemInfo = ref<SystemInfo | null>(null)
const models = ref<ModelItem[]>([])
const isLoadingModels = ref(false)
const modelsError = ref<string | null>(null)
const dimensions = ref<DimensionItem[]>([])

// 场景过滤器
const scenarioFilters = [
  { id: 'all', name: '全部模型' },
  { id: 'streaming', name: '支持流式' },
  { id: 'offline', name: '高精度离线' },
  { id: 'cpu', name: '纯 CPU 极速' },
]
const activeScenarioTag = ref('all')

const filteredModels = computed(() => {
  if (activeScenarioTag.value === 'streaming') {
    return models.value.filter(m => m.supports_streaming)
  }
  if (activeScenarioTag.value === 'offline') {
    return models.value.filter(m => !m.supports_streaming)
  }
  if (activeScenarioTag.value === 'cpu') {
    return models.value.filter(m => m.mac_backend.includes('CPU'))
  }
  return models.value
})

function toggleScenarioFilter(tagId: string) {
  activeScenarioTag.value = tagId
}

async function loadModels() {
  isLoadingModels.value = true
  modelsError.value = null
  try {
    const modResp = await fetch('/api/models')
    if (!modResp.ok) throw new Error(`HTTP 响应状态码: ${modResp.status}`)
    const data = await modResp.json()
    models.value = data
  } catch (e: any) {
    console.error('加载模型列表失败:', e)
    modelsError.value = e.message || '加载模型失败，请检查后端服务是否正常运行'
  } finally {
    isLoadingModels.value = false
  }
}

// 能力探索状态与文件/录音限制
const exploreModelKey = ref('whisper-turbo')
const exploreLang = ref('zh')
const exploreRefText = ref('')
const selectedAudioFile = ref<File | null>(null)
const fileUploadError = ref<string | null>(null)
const isTranscribing = ref(false)
const exploreResult = ref<any>(null)

const ALLOWED_AUDIO_EXTS = ['.wav', '.mp3', '.flac', '.m4a', '.ogg']

// 麦克风录音状态
const audioInputMode = ref<'upload' | 'record'>('upload')
const isRecording = ref(false)
const recordDuration = ref(0)
const recordedAudioUrl = ref<string | null>(null)
const audioVisualizerData = ref<number[]>(Array(24).fill(4))

let mediaStream: MediaStream | null = null
let audioCtx: AudioContext | null = null
let analyser: AnalyserNode | null = null
let scriptProcessor: ScriptProcessorNode | null = null
let pcmDataChunks: Float32Array[] = []
let recordTimer: any = null
let visualizerTimer: any = null

function setAudioInputMode(mode: 'upload' | 'record') {
  audioInputMode.value = mode
  fileUploadError.value = null
}

function encodeWav(samples: Float32Array, sampleRate: number): Blob {
  const buffer = new ArrayBuffer(44 + samples.length * 2)
  const view = new DataView(buffer)

  const writeString = (offset: number, str: string) => {
    for (let i = 0; i < str.length; i++) {
      view.setUint8(offset + i, str.charCodeAt(i))
    }
  }

  writeString(0, 'RIFF')
  view.setUint32(4, 36 + samples.length * 2, true)
  writeString(8, 'WAVE')
  writeString(12, 'fmt ')
  view.setUint32(16, 16, true)
  view.setUint16(20, 1, true) // PCM 格式
  view.setUint16(22, 1, true) // 单声道
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, sampleRate * 2, true) // 字节率 (16-bit mono = 2 bytes/sample)
  view.setUint16(32, 2, true) // 块对齐
  view.setUint16(34, 16, true) // 16-bit
  writeString(36, 'data')
  view.setUint32(40, samples.length * 2, true)

  let offset = 44
  for (let i = 0; i < samples.length; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]))
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true)
    offset += 2
  }

  return new Blob([buffer], { type: 'audio/wav' })
}

async function startRecording() {
  fileUploadError.value = null
  recordedAudioUrl.value = null
  pcmDataChunks = []
  recordDuration.value = 0

  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        sampleRate: 16000,
        echoCancellation: true,
        noiseSuppression: true,
      }
    })

    const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext
    audioCtx = new AudioContextClass({ sampleRate: 16000 })
    const source = audioCtx.createMediaStreamSource(mediaStream)

    analyser = audioCtx.createAnalyser()
    analyser.fftSize = 64
    source.connect(analyser)

    scriptProcessor = audioCtx.createScriptProcessor(4096, 1, 1)
    scriptProcessor.onaudioprocess = (e) => {
      if (!isRecording.value) return
      const inputBuffer = e.inputBuffer.getChannelData(0)
      pcmDataChunks.push(new Float32Array(inputBuffer))
    }
    source.connect(scriptProcessor)
    scriptProcessor.connect(audioCtx.destination)

    isRecording.value = true

    recordTimer = setInterval(() => {
      recordDuration.value += 1
    }, 1000)

    const freqData = new Uint8Array(analyser.frequencyBinCount)
    visualizerTimer = setInterval(() => {
      if (!analyser || !isRecording.value) return
      analyser.getByteFrequencyData(freqData)
      const bars = []
      const step = Math.floor(freqData.length / 24) || 1
      for (let i = 0; i < 24; i++) {
        const val = freqData[i * step] || 0
        bars.push(Math.round((val / 255) * 28) + 4)
      }
      audioVisualizerData.value = bars
    }, 80)

  } catch (err: any) {
    console.error('麦克风获取失败:', err)
    fileUploadError.value = '无法访问麦克风，请在浏览器地址栏允许麦克风访问权限。'
  }
}

function stopRecording() {
  if (!isRecording.value) return
  isRecording.value = false

  if (recordTimer) clearInterval(recordTimer)
  if (visualizerTimer) clearInterval(visualizerTimer)
  audioVisualizerData.value = Array(24).fill(4)

  if (scriptProcessor) {
    scriptProcessor.disconnect()
    scriptProcessor = null
  }
  if (mediaStream) {
    mediaStream.getTracks().forEach(t => t.stop())
    mediaStream = null
  }

  const totalLength = pcmDataChunks.reduce((acc, c) => acc + c.length, 0)
  const mergedSamples = new Float32Array(totalLength)
  let offset = 0
  for (const chunk of pcmDataChunks) {
    mergedSamples.set(chunk, offset)
    offset += chunk.length
  }

  const sampleRate = audioCtx ? audioCtx.sampleRate : 16000
  if (audioCtx) {
    audioCtx.close()
    audioCtx = null
  }

  if (totalLength === 0) {
    fileUploadError.value = '未检测到有效声音输入，请重新尝试录音。'
    return
  }

  const wavBlob = encodeWav(mergedSamples, sampleRate)
  recordedAudioUrl.value = URL.createObjectURL(wavBlob)

  const recordedFile = new File([wavBlob], `mic_${Date.now()}.wav`, { type: 'audio/wav' })
  selectedAudioFile.value = recordedFile
}

function formatRecordTime(sec: number) {
  const m = Math.floor(sec / 60).toString().padStart(2, '0')
  const s = (sec % 60).toString().padStart(2, '0')
  return `${m}:${s}`
}

function handleFileUpload(event: Event) {
  const target = event.target as HTMLInputElement
  fileUploadError.value = null
  if (target.files && target.files.length > 0) {
    const file = target.files[0]
    const ext = '.' + file.name.split('.').pop()?.toLowerCase()
    if (!ALLOWED_AUDIO_EXTS.includes(ext)) {
      fileUploadError.value = `文件格式不支持: ${ext}。仅支持音频文件 (${ALLOWED_AUDIO_EXTS.join(', ')})，请勿上传视频或其它格式。`
      target.value = ''
      selectedAudioFile.value = null
      return
    }
    selectedAudioFile.value = file
  }
}

async function submitExploreTranscribe() {
  if (!selectedAudioFile.value) return
  isTranscribing.value = true
  exploreResult.value = null

  try {
    const formData = new FormData()
    formData.append('model_key', exploreModelKey.value)
    formData.append('language', exploreLang.value)
    if (exploreRefText.value) {
      formData.append('reference_text', exploreRefText.value)
    }
    formData.append('audio_file', selectedAudioFile.value)

    const resp = await fetch('/api/asr/transcribe', {
      method: 'POST',
      body: formData,
    })
    const data = await resp.json()
    if (!resp.ok) {
      exploreResult.value = {
        audio_file: null,
        result: {
          success: false,
          error: data.detail || `转写请求失败 (HTTP ${resp.status})`,
          text: '',
          elapsed_ms: 0,
          rtf: 0,
          memory_peak_mb: 0,
        },
      }
    } else {
      exploreResult.value = data
    }
  } catch (err: any) {
    exploreResult.value = {
      audio_file: null,
      result: {
        success: false,
        error: err?.message || '网络连接或服务器异常',
        text: '',
        elapsed_ms: 0,
        rtf: 0,
        memory_peak_mb: 0,
      },
    }
  } finally {
    isTranscribing.value = false
  }
}

function jumpToExplore(key: string) {
  exploreModelKey.value = key
  activeTab.value = 'explore'
}

// 评测横评状态
const selectedDimension = ref('01-mandarin')
const selectedModelKeys = ref<string[]>(['whisper-turbo', 'sensevoice-small'])
const selectedRepeats = ref(1)
const benchmarkMode = ref('offline')
const isRunningJob = ref(false)
const activeJob = ref<any>(null)

async function checkActiveJob() {
  try {
    const resp = await fetch('/api/asr/compare/active-job')
    const data = await resp.json()
    if (data && (data.status === 'running' || data.status === 'stopping')) {
      activeJob.value = data
      isRunningJob.value = true
      pollJob(data.job_id)
    }
  } catch (err) {
    console.error('检查当前运行作业失败:', err)
  }
}

async function stopActiveJob() {
  if (!activeJob.value) return
  try {
    await fetch(`/api/asr/compare/jobs/${activeJob.value.job_id}/stop`, { method: 'POST' })
  } catch (e) {
    console.error('发送停止信号失败:', e)
  }
}

function viewJobDetail(job: any) {
  activeJob.value = job
  selectedAnalysisAudio.value = ''
  activeTab.value = 'analysis'
}

// 多维结果分析看板状态
const analysisSubTab = ref<'leaderboard' | 'charts' | 'diff' | 'errors' | 'raw'>('leaderboard')
const analysisSortBy = ref<'cer' | 'rtf' | 'memory' | 'name'>('cer')
const selectedAnalysisAudio = ref<string>('')

function switchAnalysisJob(jobId: string) {
  const job = jobHistory.value.find(j => j.job_id === jobId)
  if (job) {
    activeJob.value = job
    selectedAnalysisAudio.value = ''
  }
}

// 批次音频文件去重列表
const analysisAudioList = computed<string[]>(() => {
  if (!activeJob.value || !activeJob.value.tasks) return []
  const set = new Set<string>()
  for (const t of activeJob.value.tasks) {
    if (t.audio_file) {
      set.add(t.audio_file.split('/').pop() || t.audio_file)
    }
  }
  return Array.from(set)
})

// 当前音频对比任务明细
const currentDiffTasks = computed(() => {
  if (!activeJob.value || !activeJob.value.tasks) return []
  const audio = selectedAnalysisAudio.value || analysisAudioList.value[0]
  if (!audio) return []
  return activeJob.value.tasks.filter((t: any) => (t.audio_file.split('/').pop() || t.audio_file) === audio)
})

// 模型多维聚合统计数据
interface ModelAggregatedStat {
  model_key: string
  model_name: string
  task_count: number
  success_count: number
  avg_cer: number
  min_cer: number
  max_cer: number
  avg_rtf: number
  avg_elapsed_ms: number
  peak_memory_mb: number
  total_sub: number
  total_del: number
  total_ins: number
  total_errors: number
  badge: { title: string; color: string; desc: string }
  cer_level: { label: string; color: string }
  rtf_level: { label: string; color: string }
  meta?: ModelItem
}

const aggregatedModelStats = computed<ModelAggregatedStat[]>(() => {
  if (!activeJob.value || !activeJob.value.tasks) return []

  const group: Record<string, any[]> = {}
  for (const t of activeJob.value.tasks) {
    if (!group[t.model_key]) group[t.model_key] = []
    group[t.model_key].push(t)
  }

  const list: ModelAggregatedStat[] = []

  for (const [mKey, tasks] of Object.entries(group)) {
    const successTasks = tasks.filter(t => t.status === 'success' && t.result)
    const count = tasks.length
    const successCount = successTasks.length

    let sumCer = 0
    let minCer = 100
    let maxCer = 0
    let sumRtf = 0
    let sumElapsed = 0
    let peakMem = 0
    let totalSub = 0
    let totalDel = 0
    let totalIns = 0

    for (const t of successTasks) {
      const res = t.result
      const cer = (res.metrics?.cer ?? 0) * 100
      sumCer += cer
      if (cer < minCer) minCer = cer
      if (cer > maxCer) maxCer = cer

      sumRtf += res.rtf || 0
      sumElapsed += res.elapsed_ms || 0
      if ((res.memory_peak_mb || 0) > peakMem) peakMem = res.memory_peak_mb || 0

      if (res.metrics) {
        totalSub += res.metrics.substitutions || 0
        totalDel += res.metrics.deletions || 0
        totalIns += res.metrics.insertions || 0
      }
    }

    const avgCer = successCount > 0 ? sumCer / successCount : 0
    const avgRtf = successCount > 0 ? sumRtf / successCount : 0
    const avgElapsed = successCount > 0 ? sumElapsed / successCount : 0
    const modelMeta = models.value.find(m => m.key === mKey)
    const modelName = modelMeta?.name || mKey

    // CER 准确率评级
    let cerLevel = { label: '极佳 (0~2%)', color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30' }
    if (avgCer > 15) {
      cerLevel = { label: '较差 (>15%)', color: 'text-rose-400 bg-rose-500/10 border-rose-500/30' }
    } else if (avgCer > 5) {
      cerLevel = { label: '一般 (5~15%)', color: 'text-amber-400 bg-amber-500/10 border-amber-500/30' }
    } else if (avgCer > 2) {
      cerLevel = { label: '优良 (2~5%)', color: 'text-sky-400 bg-sky-500/10 border-sky-500/30' }
    }

    // RTF 实时率评级
    let rtfLevel = { label: '超实时极速 (<0.5x)', color: 'text-emerald-400' }
    if (avgRtf > 5.0) {
      rtfLevel = { label: '重度极慢 (>5.0x)', color: 'text-rose-400' }
    } else if (avgRtf > 1.0) {
      rtfLevel = { label: '慢于实时 (>1.0x)', color: 'text-amber-400' }
    } else if (avgRtf > 0.5) {
      rtfLevel = { label: '接近实时 (0.5~1.0x)', color: 'text-sky-400' }
    }

    list.push({
      model_key: mKey,
      model_name: modelName,
      task_count: count,
      success_count: successCount,
      avg_cer: avgCer,
      min_cer: minCer === 100 ? 0 : minCer,
      max_cer: maxCer,
      avg_rtf: avgRtf,
      avg_elapsed_ms: avgElapsed,
      peak_memory_mb: peakMem,
      total_sub: totalSub,
      total_del: totalDel,
      total_ins: totalIns,
      total_errors: totalSub + totalDel + totalIns,
      badge: { title: '常规评测', color: 'bg-slate-800/80 text-slate-400 border-slate-700/60', desc: '' },
      cer_level: cerLevel,
      rtf_level: rtfLevel,
      meta: modelMeta,
    })
  }

  // 综合评选特征勋章
  if (list.length > 0) {
    const sortedByCer = [...list].sort((a, b) => a.avg_cer - b.avg_cer)
    const sortedByRtf = [...list].sort((a, b) => a.avg_rtf - b.avg_rtf)
    const sortedByMem = [...list].sort((a, b) => a.peak_memory_mb - b.peak_memory_mb)

    const bestCer = sortedByCer[0]
    const bestRtf = sortedByRtf[0]
    const bestMem = sortedByMem[0]

    for (const item of list) {
      if (item.model_key === bestCer.model_key && item.avg_cer <= 3.0) {
        item.badge = { title: '综合精度第一 👑', color: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40', desc: '字错误率最低，识别最精准' }
      } else if (item.model_key === bestRtf.model_key) {
        item.badge = { title: '端侧极速先锋 ⚡️', color: 'bg-amber-500/20 text-amber-300 border-amber-500/40', desc: '推理速度最快，RTF 最低' }
      } else if (item.model_key === bestMem.model_key) {
        item.badge = { title: '轻量低开销 🪶', color: 'bg-sky-500/20 text-sky-300 border-sky-500/40', desc: '显存/内存峰值最小' }
      } else if (item.avg_cer <= 5.0 && item.avg_rtf <= 3.0) {
        item.badge = { title: '综合均衡优选 🌟', color: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/40', desc: '速度与准确率良好均衡' }
      } else {
        item.badge = { title: '常规表现', color: 'bg-slate-800/80 text-slate-400 border-slate-700/60', desc: '' }
      }
    }
  }

  // 排序
  list.sort((a, b) => {
    if (analysisSortBy.value === 'cer') return a.avg_cer - b.avg_cer
    if (analysisSortBy.value === 'rtf') return a.avg_rtf - b.avg_rtf
    if (analysisSortBy.value === 'memory') return a.peak_memory_mb - b.peak_memory_mb
    return a.model_key.localeCompare(b.model_key)
  })

  return list
})

async function startBenchmarkJob() {
  isRunningJob.value = true
  try {
    const resp = await fetch('/api/asr/compare/jobs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model_keys: selectedModelKeys.value,
        dimension: selectedDimension.value,
        mode: benchmarkMode.value,
        repeats: selectedRepeats.value,
      }),
    })
    const data = await resp.json()
    pollJob(data.job_id)
  } catch (err) {
    console.error(err)
    isRunningJob.value = false
  }
}

async function pollJob(jobId: string) {
  const timer = setInterval(async () => {
    try {
      const resp = await fetch(`/api/asr/compare/jobs/${jobId}`)
      const data = await resp.json()
      activeJob.value = data
      if (data.status === 'completed' || data.status === 'stopped' || data.status === 'failed' || data.status === 'interrupted') {
        clearInterval(timer)
        isRunningJob.value = false
        loadHistory()
      }
    } catch (e) {
      clearInterval(timer)
      isRunningJob.value = false
    }
  }, 1000)
}

// 历史记录
const jobHistory = ref<any[]>([])
const isLoadingHistory = ref(false)
let historyPollTimer: any = null

async function loadHistory() {
  isLoadingHistory.value = true
  try {
    const resp = await fetch('/api/comparisons?page=1&limit=20')
    const data = await resp.json()
    jobHistory.value = data.items || []
    if (!activeJob.value && jobHistory.value.length > 0) {
      activeJob.value = jobHistory.value[0]
    }

    // 智能轮询：如果列表中存在运行中或中断的任务，自动低频轮询；若都已结束则停止
    const hasRunning = jobHistory.value.some(j => j.status === 'running' || j.status === 'stopping')
    if (hasRunning) {
      if (!historyPollTimer) {
        historyPollTimer = setInterval(() => {
          loadHistory()
        }, 3000)
      }
    } else {
      if (historyPollTimer) {
        clearInterval(historyPollTimer)
        historyPollTimer = null
      }
    }
  } catch (err) {
    console.error(err)
  } finally {
    isLoadingHistory.value = false
  }
}

async function deleteJob(jobId: string) {
  try {
    await fetch(`/api/comparisons/${jobId}`, { method: 'DELETE' })
    loadHistory()
  } catch (err) {
    console.error(err)
  }
}

onMounted(async () => {
  // 加载系统状态
  try {
    const sysResp = await fetch('/api/system')
    systemInfo.value = await sysResp.json()
  } catch (e) {}

  // 加载模型列表
  await loadModels()

  // 加载测试集维度
  try {
    const dimResp = await fetch('/api/testset/dimensions')
    dimensions.value = await dimResp.json()
  } catch (e) {}

  // 加载历史快照与活跃作业检查
  loadHistory()
  checkActiveJob()
})
</script>
