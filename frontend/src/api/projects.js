import request from '@/utils/api'

export function getProjectCenter(params) {
  return request({ url: '/projects/center/', method: 'get', params })
}

export function createProjectCenter(data) {
  return request({ url: '/projects/center/', method: 'post', data })
}

export function updateProjectCenter(id, data) {
  return request({ url: `/projects/center/${id}/`, method: 'patch', data })
}

export function deleteProjectCenter(id) {
  return request({ url: `/projects/center/${id}/`, method: 'delete' })
}

export function getProjectMembers(id) {
  return request({ url: `/projects/${id}/members/`, method: 'get' })
}

export function addProjectMember(id, data) {
  return request({ url: `/projects/${id}/members/add/`, method: 'post', data })
}

export function removeProjectMember(id, memberId) {
  return request({ url: `/projects/${id}/members/${memberId}/`, method: 'delete' })
}
