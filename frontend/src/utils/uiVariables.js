const types = ['string', 'number', 'boolean', 'array', 'object']

export const loadUiVariables = (variables = []) => variables.map(variable => ({
  ...variable,
  // 非字符串值在表单中转成 JSON 文本，供用户编辑后再按类型还原。
  _originalValue: variable.value,
  value: typeof variable.value === 'string' ? variable.value : JSON.stringify(variable.value)
}))

export const formatUiVariables = (variables = []) => {
  const names = new Set()
  return variables.map((variable, index) => {
    const { name, type, description = '' } = variable
    if (typeof name !== 'string' || !/^[A-Za-z_][A-Za-z0-9_]*$/.test(name) || !types.includes(type)) {
      throw new Error(`Variable ${index + 1}: invalid name or type`)
    }
    const key = name
    if (names.has(key)) throw new Error(`Duplicate variable: ${key}`)
    names.add(key)
    let value = variable.value
    if (type === 'string' && value === 'null' && variable._originalValue === null) value = null
    const expression = typeof value === 'string' && /^(\{\{[\s\S]*\}\}|\$\{[\s\S]*\})$/.test(value)
    if (type !== 'string' && !expression) {
      try {
        value = JSON.parse(value)
      } catch {
        throw new Error(`${key}: invalid ${type} value`)
      }
      const valid = value === null || (
        type === 'number' ? typeof value === 'number' && Number.isFinite(value)
          : type === 'boolean' ? typeof value === 'boolean'
            : type === 'array' ? Array.isArray(value)
              : typeof value === 'object' && !Array.isArray(value)
      )
      if (!valid) throw new Error(`${key}: value must be ${type}`)
    }
    return { name, type, value, description }
  })
}
