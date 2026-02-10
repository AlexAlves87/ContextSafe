/**
 * Sidebar - Navigation sidebar
 *
 * Traceability:
 * - Contract: CNT-UI-COMP-016
 */

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import clsx from 'clsx';

interface SidebarProps {
  currentPath: string;
  collapsed?: boolean;
  onToggle?: () => void;
  className?: string;
}

interface NavItem {
  path: string;
  label: string;
  icon: React.ReactNode;
}

const NAV_ITEMS: NavItem[] = [
  {
    path: '/projects',
    label: 'Proyectos',
    icon: (
      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
        <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
      </svg>
    ),
  },
  {
    path: '/glossary',
    label: 'Glosario',
    icon: (
      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
        <path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z" />
      </svg>
    ),
  },
  {
    path: '/settings',
    label: 'Configuracion',
    icon: (
      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
        <path
          fillRule="evenodd"
          d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z"
          clipRule="evenodd"
        />
      </svg>
    ),
  },
];

export const Sidebar: React.FC<SidebarProps> = ({
  currentPath,
  collapsed = false,
  onToggle,
  className,
}) => {
  const location = useLocation();
  const activePath = currentPath || location.pathname;

  return (
    <aside
      className={clsx(
        'flex flex-col h-full',
        'bg-sidebar',
        'border-r border-sidebar-border',
        'transition-all duration-200',
        {
          'w-64': !collapsed,
          'w-16': collapsed,
        },
        className
      )}
    >
      {/* Toggle button */}
      <div className="p-2">
        <button
          type="button"
          onClick={onToggle}
          className={clsx(
            'w-full p-2 rounded',
            'text-sidebar-foreground hover:text-accent-foreground',
            'hover:bg-accent',
            'focus:outline-none focus:ring-2 focus:ring-ring',
            'transition-colors duration-150'
          )}
          aria-label={collapsed ? 'Expandir sidebar' : 'Colapsar sidebar'}
        >
          <svg
            className={clsx('w-5 h-5 mx-auto transition-transform', {
              'rotate-180': collapsed,
            })}
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"
              clipRule="evenodd"
            />
          </svg>
        </button>
      </div>

      {/* Navigation */}
      <nav
        className="flex-1 px-2 py-4 space-y-1"
        role="navigation"
        aria-label="Navegación principal"
      >
        {NAV_ITEMS.map((item) => {
          const isActive = activePath.startsWith(item.path);

          return (
            <Link
              key={item.path}
              to={item.path}
              className={clsx(
                'flex items-center gap-3 px-3 py-2 rounded',
                'transition-all duration-150',
                'focus:outline-none focus:ring-2 focus:ring-ring',
                {
                  'bg-sidebar-active text-sidebar-active-foreground':
                    isActive,
                  'text-sidebar-foreground hover:bg-accent hover:text-accent-foreground':
                    !isActive,
                  'justify-center': collapsed,
                }
              )}
              title={collapsed ? item.label : undefined}
            >
              <span className={clsx({ 'text-sidebar-active-foreground': isActive })}>
                {item.icon}
              </span>
              {!collapsed && (
                <span className="text-sm font-medium">{item.label}</span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-sidebar-border">
        {!collapsed && (
          <div className="text-xs text-muted-foreground">
            <p className="font-medium">ContextSafe v0.1.0</p>
            <p className="mt-1">100% Local</p>
          </div>
        )}
      </div>
    </aside>
  );
};

export default Sidebar;
