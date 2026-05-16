export const zh = {
  shell: {
    label: "NAS CPU Console",
    title: "Pixloom",
    copy: "本地模型、本地队列、本地结果。提交后后台串行处理，手机端只保留最短操作路径。",
    metrics: {
      operator: "当前开放",
      installed: "本地文件",
    },
  },
  panels: {
    input: {
      eyebrow: "输入",
      title: "提交任务",
      copy: "图片会先落到本地输入目录，再进入后台任务队列。",
    },
    model: {
      eyebrow: "模型",
      title: "选择模型",
      copy: "先按用途选，再看当前模型的提醒、速度和锐评。",
    },
    output: {
      eyebrow: "输出",
      title: "输出尺寸与保存",
      copy: "先选最终最长边，再选保存格式。JPG / WEBP 质量固定 100，原始模式会按模型自己的倍率输出。",
    },
    receipt: {
      eyebrow: "回执",
      title: "当前结果",
      copy: "这里收口批次回执和当前选中任务的预览，不把队列细节塞进同一块区域。",
    },
    task: {
      eyebrow: "队列",
      title: "任务状态",
      copy: "任务状态从 SQLite 回读。详情、列表和完成图都压成短区块，方便手机上扫一眼。",
    },
    log: {
      eyebrow: "跟踪",
      title: "请求日志",
      copy: "每条请求的 JSONL 审计片段，按 request_id 回溯。失败时优先检查这里。",
    },
  },
  taskStatus: {
    queued: "排队中",
    running: "处理中",
    completed: "已完成",
    failed: "失败",
    deleted: "已删除",
    interrupted: "已中断",
  },
  upload: {
    placeholder: "拖拽图片到此处或点击上传",
    formats: "PNG · JPG · JPEG · WEBP",
    maxSize: "单文件最大 25 MB",
    addMore: "添加更多图片",
    selected: "已选择 {count} 个文件",
    remove: "移除",
  },
  model: {
    select: "请选择一个模型后查看建议",
    noModels: "当前没有检测到已安装模型。请把模型文件放到 models/ 目录后重启应用。",
    noOperatorReady:
      "当前本地已有模型，但还没有已验收并开放给日常操作的模型。请先完成本机验收，或调整开放状态后重启应用。",
    unavailable: "当前选择的模型不可用，请重新选择。",
    hiddenNote: "当前仅显示已验收模型；另有 {count} 个本地模型仍在评估中。",
    speed: {
      fast: "较快",
      normal: "普通",
      slow: "普通偏慢",
      verySlow: "很慢",
    },
  },
  submit: {
    label: "提交任务",
    loading: "提交中...",
  },
  refresh: {
    label: "刷新任务",
  },
  delete: {
    label: "删除所选任务",
    confirm: "删除所选任务会同时移除关联的本地输入和输出图片文件。",
  },
  empty: {
    noTasks: "还没有提交过任务。上传图片并提交后，这里会显示排队、处理中、完成和失败状态。",
    noTaskSelected: "请在任务列表里选择任务。这里会显示所选任务的详细状态、路径和错误信息。",
    noLogs: "当前请求还没有日志片段。",
    taskNotFound: "没有找到这条任务，列表可能已经刷新或任务已被删除。",
  },
  detail: {
    taskDetail: "所选任务详情",
    deleteNote: "删除所选任务会同时移除关联的本地输入和输出图片文件。",
  },
  format: {
    png: "PNG",
    jpg: "JPG",
    webp: "WEBP",
  },
  toast: {
    deleteSuccess: "已删除任务，移除了关联文件。",
    deleteFailed: "删除失败，请重试。",
    submitFailed: "批次创建失败，请检查文件后重试。",
  },
  progress: {
    processingComplete: "处理完成",
    processingFailed: "处理失败",
    waitingForWorker: "等待后台处理",
    estimatedRemaining: "预计剩余 {eta}",
  },
};
