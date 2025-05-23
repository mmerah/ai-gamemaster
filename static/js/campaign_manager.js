/**
 * Campaign Manager JavaScript
 * Handles the campaign and character template management interface
 */

class CampaignManager {
    constructor() {
        this.currentTab = 'campaigns';
        this.campaigns = [];
        this.templates = [];
        this.d5eRaces = [];
        this.d5eClasses = [];
        this.selectedTemplates = new Set();
        
        this.init();
    }

    async init() {
        this.bindEvents();
        await this.loadInitialData();
        this.renderCurrentTab();
    }

    bindEvents() {
        // Tab switching
        document.getElementById('campaigns-tab').addEventListener('click', () => {
            this.switchTab('campaigns');
        });
        
        document.getElementById('templates-tab').addEventListener('click', () => {
            this.switchTab('templates');
        });

        // New campaign/template buttons
        document.getElementById('new-campaign-btn').addEventListener('click', () => {
            this.showCampaignModal();
        });
        
        document.getElementById('new-template-btn').addEventListener('click', () => {
            this.showTemplateModal();
        });

        // Modal close buttons
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.closeModal(e.target.closest('.modal'));
            });
        });

        // Form submissions
        document.getElementById('campaign-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleCampaignSubmit();
        });
        
        document.getElementById('template-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleTemplateSubmit();
        });

        // Modal backdrop clicks
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal(modal);
                }
            });
        });

        // Empty state buttons
        document.querySelectorAll('.empty-action').forEach(btn => {
            btn.addEventListener('click', () => {
                if (this.currentTab === 'campaigns') {
                    this.showCampaignModal();
                } else {
                    this.showTemplateModal();
                }
            });
        });
    }

    async loadInitialData() {
        this.showLoading(true);
        
        try {
            // Load campaigns, templates, and D&D 5e data concurrently
            const [campaignsResponse, templatesResponse, racesResponse, classesResponse] = await Promise.all([
                fetch('/api/campaigns'),
                fetch('/api/character_templates'),
                fetch('/api/d5e/races'),
                fetch('/api/d5e/classes')
            ]);

            if (campaignsResponse.ok) {
                const campaignsData = await campaignsResponse.json();
                this.campaigns = campaignsData.campaigns || [];
            }

            if (templatesResponse.ok) {
                const templatesData = await templatesResponse.json();
                this.templates = templatesData.templates || [];
            }

            if (racesResponse.ok) {
                const racesData = await racesResponse.json();
                this.d5eRaces = racesData.races || [];
            }

            if (classesResponse.ok) {
                const classesData = await classesResponse.json();
                this.d5eClasses = classesData.classes || [];
            }

        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showNotification('Error loading data. Please refresh the page.', 'error');
        }
        
        this.showLoading(false);
    }

    switchTab(tabName) {
        // Update active tab
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');

        // Update active section
        document.querySelectorAll('.cm-section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(`${tabName}-section`).classList.add('active');

        this.currentTab = tabName;
        this.renderCurrentTab();
    }

    renderCurrentTab() {
        if (this.currentTab === 'campaigns') {
            this.renderCampaigns();
        } else {
            this.renderTemplates();
        }
    }

    renderCampaigns() {
        const grid = document.getElementById('campaigns-grid');
        const emptyState = document.getElementById('campaigns-empty');

        if (this.campaigns.length === 0) {
            grid.style.display = 'none';
            emptyState.style.display = 'block';
            return;
        }

        grid.style.display = 'grid';
        emptyState.style.display = 'none';

        grid.innerHTML = this.campaigns.map(campaign => this.createCampaignCard(campaign)).join('');

        // Bind card events
        this.bindCampaignCardEvents();
    }

    renderTemplates() {
        const grid = document.getElementById('templates-grid');
        const emptyState = document.getElementById('templates-empty');

        if (this.templates.length === 0) {
            grid.style.display = 'none';
            emptyState.style.display = 'block';
            return;
        }

        grid.style.display = 'grid';
        emptyState.style.display = 'none';

        grid.innerHTML = this.templates.map(template => this.createTemplateCard(template)).join('');

        // Bind card events
        this.bindTemplateCardEvents();
    }

    createCampaignCard(campaign) {
        const createdDate = new Date(campaign.created_date).toLocaleDateString();
        const lastPlayed = campaign.last_played 
            ? new Date(campaign.last_played).toLocaleDateString()
            : 'Never';

        return `
            <div class="campaign-card" data-campaign-id="${campaign.id}">
                <div class="card-header">
                    <h3 class="card-title">${this.escapeHtml(campaign.name)}</h3>
                    <div class="card-actions">
                        <button class="card-action start" title="Start Campaign">
                            <span>▶</span>
                        </button>
                        <button class="card-action edit" title="Edit Campaign">
                            <span>✏️</span>
                        </button>
                        <button class="card-action delete" title="Delete Campaign">
                            <span>🗑️</span>
                        </button>
                    </div>
                </div>
                <p class="card-description">${this.escapeHtml(campaign.description)}</p>
                <div class="card-meta">
                    <span class="card-tag">Level ${campaign.starting_level}</span>
                    <span class="card-tag">${campaign.difficulty}</span>
                    <span class="card-tag">${campaign.party_size} Characters</span>
                </div>
                <div class="card-footer">
                    <span class="card-date">Created: ${createdDate}</span>
                    <span class="card-date">Last Played: ${lastPlayed}</span>
                </div>
            </div>
        `;
    }

    createTemplateCard(template) {
        return `
            <div class="template-card" data-template-id="${template.id}">
                <div class="card-header">
                    <h3 class="card-title">${this.escapeHtml(template.name)}</h3>
                    <div class="card-actions">
                        <button class="card-action edit" title="Edit Template">
                            <span>✏️</span>
                        </button>
                        <button class="card-action delete" title="Delete Template">
                            <span>🗑️</span>
                        </button>
                    </div>
                </div>
                <p class="card-description">${this.escapeHtml(template.description)}</p>
                <div class="card-meta">
                    <span class="card-tag">${template.race}</span>
                    <span class="card-tag">${template.char_class}</span>
                    <span class="card-tag">Level ${template.level}</span>
                </div>
            </div>
        `;
    }

    bindCampaignCardEvents() {
        document.querySelectorAll('.campaign-card').forEach(card => {
            const campaignId = card.dataset.campaignId;

            card.querySelector('.start').addEventListener('click', (e) => {
                e.stopPropagation();
                this.startCampaign(campaignId);
            });

            card.querySelector('.edit').addEventListener('click', (e) => {
                e.stopPropagation();
                this.editCampaign(campaignId);
            });

            card.querySelector('.delete').addEventListener('click', (e) => {
                e.stopPropagation();
                this.deleteCampaign(campaignId);
            });
        });
    }

    bindTemplateCardEvents() {
        document.querySelectorAll('.template-card').forEach(card => {
            const templateId = card.dataset.templateId;

            card.querySelector('.edit').addEventListener('click', (e) => {
                e.stopPropagation();
                this.editTemplate(templateId);
            });

            card.querySelector('.delete').addEventListener('click', (e) => {
                e.stopPropagation();
                this.deleteTemplate(templateId);
            });
        });
    }

    async showCampaignModal(campaign = null) {
        const modal = document.getElementById('campaign-modal');
        const form = document.getElementById('campaign-form');
        const title = document.getElementById('campaign-modal-title');

        // Reset form
        form.reset();
        this.selectedTemplates.clear();

        if (campaign) {
            title.textContent = 'Edit Campaign';
            this.populateCampaignForm(campaign);
        } else {
            title.textContent = 'Create New Campaign';
        }

        // Populate party selection
        await this.populatePartySelection();

        this.showModal(modal);
    }

    async populatePartySelection() {
        const partySelection = document.getElementById('party-selection');
        
        if (this.templates.length === 0) {
            partySelection.innerHTML = `
                <p style="grid-column: 1 / -1; text-align: center; color: var(--text-secondary);">
                    No character templates available. Create some templates first!
                </p>
            `;
            return;
        }

        partySelection.innerHTML = this.templates.map(template => `
            <div class="template-option" data-template-id="${template.id}">
                <h5>${this.escapeHtml(template.name)}</h5>
                <p>${template.race} ${template.char_class}</p>
            </div>
        `).join('');

        // Bind selection events
        partySelection.querySelectorAll('.template-option').forEach(option => {
            option.addEventListener('click', () => {
                const templateId = option.dataset.templateId;
                this.toggleTemplateSelection(templateId, option);
            });
        });

        this.updateSelectedCharacters();
    }

    toggleTemplateSelection(templateId, optionElement) {
        if (this.selectedTemplates.has(templateId)) {
            this.selectedTemplates.delete(templateId);
            optionElement.classList.remove('selected');
        } else {
            this.selectedTemplates.add(templateId);
            optionElement.classList.add('selected');
        }
        
        this.updateSelectedCharacters();
    }

    updateSelectedCharacters() {
        const selectedContainer = document.getElementById('selected-characters');
        
        if (this.selectedTemplates.size === 0) {
            selectedContainer.innerHTML = '<p style="color: var(--text-secondary);">No characters selected</p>';
            return;
        }

        const selectedTemplateData = Array.from(this.selectedTemplates).map(id => 
            this.templates.find(t => t.id === id)
        ).filter(Boolean);

        selectedContainer.innerHTML = selectedTemplateData.map(template => `
            <div class="selected-character">
                <span>${this.escapeHtml(template.name)}</span>
                <button type="button" class="remove" data-template-id="${template.id}">×</button>
            </div>
        `).join('');

        // Bind remove events
        selectedContainer.querySelectorAll('.remove').forEach(btn => {
            btn.addEventListener('click', () => {
                const templateId = btn.dataset.templateId;
                this.selectedTemplates.delete(templateId);
                
                // Update the option element
                const optionElement = document.querySelector(`.template-option[data-template-id="${templateId}"]`);
                if (optionElement) {
                    optionElement.classList.remove('selected');
                }
                
                this.updateSelectedCharacters();
            });
        });
    }

    async showTemplateModal(template = null) {
        const modal = document.getElementById('template-modal');
        const form = document.getElementById('template-form');
        const title = document.getElementById('template-modal-title');

        // Reset form
        form.reset();

        if (template) {
            title.textContent = 'Edit Character Template';
            this.populateTemplateForm(template);
        } else {
            title.textContent = 'Create Character Template';
        }

        // Populate race and class dropdowns
        this.populateRaceDropdown();
        this.populateClassDropdown();

        this.showModal(modal);
    }

    populateRaceDropdown() {
        const raceSelect = document.getElementById('template-race');
        raceSelect.innerHTML = '<option value="">Select Race</option>' +
            this.d5eRaces.map(race => `<option value="${race.name}">${race.name}</option>`).join('');
    }

    populateClassDropdown() {
        const classSelect = document.getElementById('template-class');
        classSelect.innerHTML = '<option value="">Select Class</option>' +
            this.d5eClasses.map(cls => `<option value="${cls.name}">${cls.name}</option>`).join('');
    }

    async handleCampaignSubmit() {
        const form = document.getElementById('campaign-form');
        const formData = new FormData(form);
        
        // Validate required fields
        if (!formData.get('name') || !formData.get('description')) {
            this.showNotification('Please fill in all required fields.', 'error');
            return;
        }

        if (this.selectedTemplates.size === 0) {
            this.showNotification('Please select at least one character for the party.', 'error');
            return;
        }

        const campaignData = {
            id: this.generateId(formData.get('name')),
            name: formData.get('name'),
            description: formData.get('description'),
            campaign_goal: formData.get('campaign_goal') || '',
            starting_location: formData.get('starting_location') || '',
            starting_level: parseInt(formData.get('starting_level')) || 1,
            difficulty: formData.get('difficulty') || 'normal',
            party_character_ids: Array.from(this.selectedTemplates),
            opening_narrative: formData.get('opening_narrative') || ''
        };

        try {
            this.showLoading(true);
            
            const response = await fetch('/api/campaigns', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(campaignData)
            });

            if (response.ok) {
                const newCampaign = await response.json();
                this.campaigns.push(newCampaign);
                this.renderCampaigns();
                this.closeModal(document.getElementById('campaign-modal'));
                this.showNotification('Campaign created successfully!', 'success');
            } else {
                const error = await response.json();
                this.showNotification(error.error || 'Failed to create campaign.', 'error');
            }
        } catch (error) {
            console.error('Error creating campaign:', error);
            this.showNotification('Error creating campaign. Please try again.', 'error');
        }
        
        this.showLoading(false);
    }

    async handleTemplateSubmit() {
        const form = document.getElementById('template-form');
        const formData = new FormData(form);
        
        // Validate required fields
        if (!formData.get('name') || !formData.get('race') || !formData.get('char_class')) {
            this.showNotification('Please fill in all required fields.', 'error');
            return;
        }

        const templateData = {
            id: this.generateId(formData.get('name')),
            name: formData.get('name'),
            race: formData.get('race'),
            char_class: formData.get('char_class'),
            level: parseInt(formData.get('level')) || 1,
            background: formData.get('background') || '',
            alignment: formData.get('alignment') || 'True Neutral',
            base_stats: {
                STR: parseInt(formData.get('str')) || 10,
                DEX: parseInt(formData.get('dex')) || 10,
                CON: parseInt(formData.get('con')) || 10,
                INT: parseInt(formData.get('int')) || 10,
                WIS: parseInt(formData.get('wis')) || 10,
                CHA: parseInt(formData.get('cha')) || 10
            },
            proficiencies: [],
            languages: [],
            starting_equipment: [],
            starting_gold: 150,
            portrait_path: null
        };

        try {
            this.showLoading(true);
            
            const response = await fetch('/api/character_templates', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(templateData)
            });

            if (response.ok) {
                const newTemplate = await response.json();
                // Add metadata for display
                const templateMeta = {
                    id: newTemplate.id,
                    name: newTemplate.name,
                    race: newTemplate.race,
                    char_class: newTemplate.char_class,
                    level: newTemplate.level,
                    description: `A ${newTemplate.race} ${newTemplate.char_class}.`,
                    file: `${newTemplate.id}.json`,
                    portrait_path: newTemplate.portrait_path
                };
                
                this.templates.push(templateMeta);
                this.renderTemplates();
                this.closeModal(document.getElementById('template-modal'));
                this.showNotification('Character template created successfully!', 'success');
            } else {
                const error = await response.json();
                this.showNotification(error.error || 'Failed to create template.', 'error');
            }
        } catch (error) {
            console.error('Error creating template:', error);
            this.showNotification('Error creating template. Please try again.', 'error');
        }
        
        this.showLoading(false);
    }

    async startCampaign(campaignId) {
        if (!confirm('Start this campaign? This will load the campaign and take you to the game.')) {
            return;
        }

        try {
            this.showLoading(true);
            
            const response = await fetch(`/api/campaigns/${campaignId}/start`, {
                method: 'POST'
            });

            if (response.ok) {
                // Redirect to the main game interface
                window.location.href = '/';
            } else {
                const error = await response.json();
                this.showNotification(error.error || 'Failed to start campaign.', 'error');
            }
        } catch (error) {
            console.error('Error starting campaign:', error);
            this.showNotification('Error starting campaign. Please try again.', 'error');
        }
        
        this.showLoading(false);
    }

    async deleteCampaign(campaignId) {
        const campaign = this.campaigns.find(c => c.id === campaignId);
        if (!campaign) return;

        if (!confirm(`Delete campaign "${campaign.name}"? This action cannot be undone.`)) {
            return;
        }

        try {
            this.showLoading(true);
            
            const response = await fetch(`/api/campaigns/${campaignId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.campaigns = this.campaigns.filter(c => c.id !== campaignId);
                this.renderCampaigns();
                this.showNotification('Campaign deleted successfully.', 'success');
            } else {
                const error = await response.json();
                this.showNotification(error.error || 'Failed to delete campaign.', 'error');
            }
        } catch (error) {
            console.error('Error deleting campaign:', error);
            this.showNotification('Error deleting campaign. Please try again.', 'error');
        }
        
        this.showLoading(false);
    }

    async deleteTemplate(templateId) {
        const template = this.templates.find(t => t.id === templateId);
        if (!template) return;

        if (!confirm(`Delete character template "${template.name}"? This action cannot be undone.`)) {
            return;
        }

        try {
            this.showLoading(true);
            
            const response = await fetch(`/api/character_templates/${templateId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.templates = this.templates.filter(t => t.id !== templateId);
                this.renderTemplates();
                this.showNotification('Character template deleted successfully.', 'success');
            } else {
                const error = await response.json();
                this.showNotification(error.error || 'Failed to delete template.', 'error');
            }
        } catch (error) {
            console.error('Error deleting template:', error);
            this.showNotification('Error deleting template. Please try again.', 'error');
        }
        
        this.showLoading(false);
    }

    // TODO: Implement edit functionality
    editCampaign(campaignId) {
        this.showNotification('Edit functionality coming soon!', 'info');
    }

    editTemplate(templateId) {
        this.showNotification('Edit functionality coming soon!', 'info');
    }

    // Utility methods
    showModal(modal) {
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    closeModal(modal) {
        modal.classList.remove('show');
        document.body.style.overflow = '';
    }

    showLoading(show) {
        const overlay = document.getElementById('loading-overlay');
        overlay.style.display = show ? 'flex' : 'none';
    }

    showNotification(message, type = 'info') {
        // Simple notification system - could be enhanced
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'error' ? '#ff4757' : type === 'success' ? '#2ed573' : '#4a9eff'};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 6px;
            z-index: 1200;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            animation: slideIn 0.3s ease;
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    generateId(name) {
        return name.toLowerCase()
            .replace(/[^a-z0-9\s-]/g, '')
            .replace(/\s+/g, '_')
            .replace(/-+/g, '_')
            .substring(0, 50);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Add CSS for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

// Initialize the campaign manager when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.campaignManager = new CampaignManager();
});
