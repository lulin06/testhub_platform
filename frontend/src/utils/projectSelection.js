import { watch } from 'vue'

const SELECTED_PROJECT_STORAGE_KEY = 'selected_project_id'

const getStorageKey = () => {
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    return `${SELECTED_PROJECT_STORAGE_KEY}:${user.id || 'anonymous'}`
  } catch (error) {
    return `${SELECTED_PROJECT_STORAGE_KEY}:anonymous`
  }
}

const normalizeProjectId = (value) => {
  if (value && typeof value === 'object') return value.id
  return value
}

const getWorkspaceProjectId = (project) =>
  normalizeProjectId(project?.workspace_project) || project?.workspace_project_id || null

const hasWorkspaceProjectReference = (project) =>
  Object.prototype.hasOwnProperty.call(project || {}, 'workspace_project') ||
  Object.prototype.hasOwnProperty.call(project || {}, 'workspace_project_id')

// 在不同业务模块之间通过统一项目ID保留最近选择；未关联统一项目时使用模块项目ID。
export const rememberSelectedProject = (projectId, projects = []) => {
  const storageKey = getStorageKey()
  if (projectId === null || projectId === undefined || projectId === '') {
    localStorage.removeItem(storageKey)
    return
  }

  const selectedProject = projects.find(project => String(project.id) === String(projectId))
  const workspaceProjectId = getWorkspaceProjectId(selectedProject)
  const preference = hasWorkspaceProjectReference(selectedProject)
    ? workspaceProjectId
      ? { workspaceProjectId: String(workspaceProjectId) }
      : { legacyProjectName: selectedProject.name }
    : { workspaceProjectId: String(projectId) }
  localStorage.setItem(storageKey, JSON.stringify(preference))
}

// 优先恢复用户最近选择的项目；项目不在当前模块候选项中时沿用页面原有默认值。
export const getPreferredProjectId = (projects = [], fallbackId = null) => {
  const savedPreference = localStorage.getItem(getStorageKey())
  if (!savedPreference) return fallbackId

  let preference
  try {
    preference = JSON.parse(savedPreference)
  } catch (error) {
    preference = { workspaceProjectId: savedPreference }
  }

  const linkedProject = preference.workspaceProjectId && projects.find(project =>
    String(getWorkspaceProjectId(project)) === preference.workspaceProjectId
  )
  if (linkedProject) return linkedProject.id

  const workspaceProject = preference.workspaceProjectId && projects.find(project =>
    !hasWorkspaceProjectReference(project) && String(project.id) === preference.workspaceProjectId
  )
  if (workspaceProject) return workspaceProject.id

  const legacyProject = preference.legacyProjectName && projects.find(project =>
    hasWorkspaceProjectReference(project) && project.name === preference.legacyProjectName
  )
  return legacyProject?.id ?? fallbackId
}

// 页面刚初始化时的空值不会覆盖之前记住的项目。
export const useRememberedProject = (projectRef, projectsRef) => {
  watch(projectRef, projectId => {
    if (projectId !== null && projectId !== undefined && projectId !== '') {
      rememberSelectedProject(projectId, projectsRef.value || [])
    }
  })
}
