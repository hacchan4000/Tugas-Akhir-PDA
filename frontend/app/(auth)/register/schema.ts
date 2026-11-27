import Joi from 'joi';

export const registerSchema = Joi.object({
  name: Joi.string().trim().min(2).max(100).required().messages({
    'string.empty': 'Nama operator wajib diisi',
    'string.min': 'Nama operator minimal 2 karakter',
    'string.max': 'Nama operator maksimal 100 karakter',
  }),
  email: Joi.string()
    .trim()
    .email({ tlds: { allow: false } })
    .max(255)
    .required()
    .messages({
      'string.empty': 'E-mail wajib diisi',
      'string.email': 'Format e-mail tidak valid',
      'string.max': 'E-mail maksimal 255 karakter',
    }),
  password: Joi.string().min(8).max(72).required().messages({
    'string.empty': 'Password wajib diisi',
    'string.min': 'Password minimal 8 karakter',
    'string.max': 'Password maksimal 72 karakter',
  }),
  confirmPassword: Joi.string().valid(Joi.ref('password')).required().messages({
    'string.empty': 'Konfirmasi password wajib diisi',
    'any.only': 'Konfirmasi password tidak cocok',
  }),
});
